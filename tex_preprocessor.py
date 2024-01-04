import re
import click
from functools import partial
import warnings
import io

from pygments import highlight
from pygments.lexer import Lexer
from pygments.lexers import Python3Lexer
from pygments.formatters import LatexFormatter
from pygments.styles import get_style_by_name
from tex_lexer import Tex3Lexer
import numpy as np
import yaml

STYLE=None
FORMATTER=None


class Document:

    def __init__(self, src:str):
        self.src = src
        self.changes = []
        self._build_line_lut()

        self.change_start = []
        self.change_end = []

    def _build_line_lut(self):
        line_lut = [0]
        pos = self.src.find('\n')
        while pos != -1:
            line_lut.append(pos+1)
            pos = self.src.find('\n', pos + 1)
        
        self.line_lut = line_lut

    def get_line_col(self, pos:int):
        assert pos >= 0
        if pos == 0:
            return 0, 0
        row = np.searchsorted(self.line_lut, pos) - 1
        col = pos - self.line_lut[row]
        return row + 1, col
    
    def add_change(self, start:int, end:int, repl:str, category:str, **kwargs):

        if len(self.change_start) > 0:
            near_start_ind = np.searchsorted(self.change_start, start, side='right')
            if near_start_ind > 0:
                near_start = self.change_start[near_start_ind - 1]
                near_end = self.change_end[near_start_ind - 1]
                if start >= near_start and start < near_end:
                    raise RuntimeError('overlapped change detected')
        
        assert end > start
        assert end <= len(self.src)

        insert_pos = 0 if len(self.change_start) == 0 else np.searchsorted(self.change_start, start)

        self.change_start.insert(insert_pos, start)
        self.change_end.insert(insert_pos, end)


        line, col = self.get_line_col(start)
        self.changes.insert(
            insert_pos,
            dict(
                start=start,
                end=end,
                org=self.src[start:end],
                repl=repl,
                category=category,
                line=int(line),
                col=int(col),
                **kwargs
            )
        )
    
    def apply_changes(self) -> dict:
        new_src = self.src
        delta = 0

        change_start = [item['start'] for item in self.changes]
        assert np.all(np.diff(change_start) >= 0)

        log = dict()

        for item in self.changes:
            pos = item['start'] + delta
            org_len = len(item['org'])
            assert new_src[pos : pos + org_len] == item['org']
            delta += len(item['repl']) - org_len
            new_src = new_src[:pos] + item['repl'] + new_src[pos + org_len:]
            
            category = item['category']
            if category not in log:
                log[category] = []
            log[category].append(item)
        

        sio = io.StringIO()
        yaml.dump(log, sio)
        return dict(
            new_src=new_src,
            log=sio.getvalue()
        )
        

def _process_inline_generic(doc:Document, inline_cmd:str, lexer:Lexer, new_cmd:str, category:str, keep_open_close=False):
    src = doc.src

    pos = src.find(inline_cmd)
    while pos != -1:
        open_char_pos = pos + len(inline_cmd)
        open_char = src[open_char_pos]
        if open_char == '{':
            close_char = '}'
        else:
            close_char = open_char
        
        pos2 = src.find(close_char, open_char_pos + 1)
        content = src[open_char_pos + 1 : pos2]

        if '\n' in content:
            warnings.warn('line break detected in inline highlight content', category=UserWarning)
        
        if lexer:
            highlighted_content = highlight(content, lexer, FORMATTER)
            # discard environment
            highlighted_content = '\n'.join(highlighted_content.split('\n')[1:-2])
        else:
            highlighted_content = content

        if keep_open_close:
            repl = f'{new_cmd}{open_char}{highlighted_content}{close_char}'
        else:
            repl = '%s{%s}' % (new_cmd, highlighted_content)

        doc.add_change(
            start=pos,
            end=pos2 + 1,
            repl=repl,
            category=category,
            open_char=open_char,
            close_char=close_char
        )

        pos = src.find(inline_cmd, pos2 + 1)


def _process_env_generic(doc:Document, env_name:str, lexer:Lexer, category:str):
    src = doc.src

    begin_cmd = '\\begin{%s}' % env_name
    end_cmd = '\\end{%s}' % env_name


    pos = src.find(begin_cmd)
    while pos != -1:
        next_end_line_pos = doc.src.find('\n', pos + len(begin_cmd))
        end_cmd_pos = doc.src.find(end_cmd, next_end_line_pos + 1)
        body = doc.src[next_end_line_pos + 1:end_cmd_pos]

        repl = ''
        repl += '\\begin{filecontents}[force]{\\jobname-lst-raw.vrb}\n%s\\end{filecontents}\n' % body
        highlighted_content = highlight(body, lexer, FORMATTER)
        repl += '\\begin{filecontents}[force]{\\jobname-lst-hl.vrb}\n%s\\end{filecontents}' % highlighted_content

        doc.add_change(
            start=pos,
            end=end_cmd_pos+len(end_cmd),
            repl=repl,
            category=category
        )

        pos = end_cmd_pos + 1


def _process(doc:Document):
    _process_env_generic(doc, 'latexsample', Tex3Lexer(), 'env:latexsample')

    # inline highlighters
    _process_inline_generic(doc, r'\inltex', Tex3Lexer(), r'\inlinestylea', 'inline:tex3')
    _process_inline_generic(doc, r'\inlpy', Python3Lexer(), r'\inlinestyleb', 'inline:python3')
    _process_inline_generic(doc, r'\inlpl', None, r'\verb', 'inlnie:verbatim', keep_open_close=True)


if __name__ == '__main__':


    def set_style(style:str):
        global STYLE, FORMATTER
        STYLE = get_style_by_name(style)
        FORMATTER = LatexFormatter(style=STYLE)

    @click.group()
    def main():
        pass

    @main.command()
    @click.argument('output')
    @click.option('-s', '--style', help='style', default='default')
    def export_style(output, style):
        set_style(style)

        with open(output, 'w') as f:
            f.write(FORMATTER.get_style_defs())


    @main.command()
    @click.argument('input')
    @click.argument('output')
    @click.option('-s', '--style', default='default')
    @click.option('-l', '--log', default=None, help='log file')
    @click.option('-p', '--protect', help='fill the output document with protection pattern', is_flag=True)
    def process(input, output, style, log, protect):
        set_style(style)

        with open(input) as f:
            src = f.read()

        doc = Document(src)
        _process(doc)

        ret = doc.apply_changes()
        with open(output, 'w') as f:
            f.write(ret['new_src'])

        if log:
            with open(log, 'w') as f:
                f.write(ret['log'])

    main()

    
    
