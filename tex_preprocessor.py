import re
import click
from functools import partial
import warnings
import io
from typing import Callable
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

COMMENT_RE = re.compile(r'(?<!\\)%')
TEX3_SOURCE_CODE_ENVS = [
    'latexsample',
    'latexsample*',
    'latexsample**'
]


class Document:

    def __init__(self, src:str):
        self.src = src
        self.applied_changes = []
        self.skipped_changes = []


    def is_commented(self, pos:int) -> int:
        prev_line_pos = self.src.rfind('\n', 0, pos)
        content_ahead = self.src[prev_line_pos + 1:pos].lstrip()
        if COMMENT_RE.search(content_ahead):
            return True
        return False



    def apply_change(self, start:int, end:int, repl:str, category:str, apply_to_comments=False, **kwargs) -> int:

        prev_line_pos = max(self.src.rfind('\n', 0, start), 0)
        this_line_end = self.src.find('\n', start)
        if this_line_end == -1:
            this_line_end == len(self.src)

        change_item = dict(
            start=start,
            end=end,
            original=self.src[start:end],
            repl=repl,
            category=category,
            line=self.src[prev_line_pos+1:this_line_end].lstrip(),
            **kwargs
        )

        if not apply_to_comments:
            if self.is_commented(start):
                self.skipped_changes.append(change_item)
                return end # no change will happen in this case

        self.applied_changes.append(change_item)

        new_src = self.src[:start] + repl + self.src[end:]
        self.src = new_src

        return start + len(repl)


    def get_log(self) -> str:
        sio = io.StringIO()
        yaml.dump(dict(
            applied_changes=self.applied_changes,
            skipped_changes=self.skipped_changes), sio)
        return sio.getvalue()

    
def _process_inline_generic(doc:Document, inline_cmd:str, lexer:Lexer, new_cmd:str, category:str, keep_open_close=False):

    pos = doc.src.find(inline_cmd)
    while pos != -1:
        open_char_pos = pos + len(inline_cmd)
        open_char = doc.src[open_char_pos]
        if open_char == '{':
            close_char = '}'
        else:
            close_char = open_char
        
        pos2 = doc.src.find(close_char, open_char_pos + 1)
        content = doc.src[open_char_pos + 1 : pos2]

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

        next_pos = doc.apply_change(
            start=pos,
            end=pos2 + 1,
            repl=repl,
            category=category,
            open_char=open_char,
            close_char=close_char
        )

        pos = doc.src.find(inline_cmd, next_pos)


def _process_env_generic(doc:Document, env_name:str, lexer:Lexer, category:str):
    begin_cmd = '\\begin{%s}' % env_name
    end_cmd = '\\end{%s}' % env_name

    pos = doc.src.find(begin_cmd)
    while pos != -1:

        if doc.is_commented(pos):
            pos = doc.src.find(begin_cmd, pos + len(begin_cmd))
            continue
        
        next_end_line_pos = doc.src.find('\n', pos + len(begin_cmd))
        end_cmd_pos = doc.src.find(end_cmd, next_end_line_pos + 1)
        assert end_cmd_pos != -1
        body = doc.src[next_end_line_pos + 1:end_cmd_pos]

        repl = '\\def\CurrentEnvName{%s}\n' % env_name
        repl += '\\begin{filecontents}[force,noheader]{\\jobname-lst-raw.vrb}\n%s\\end{filecontents}\n' % body
        highlighted_content = highlight(body, lexer, FORMATTER)
        repl += '\\begin{filecontents}[force,noheader]{\\jobname-lst-hl.vrb}\n%s\\end{filecontents}' % highlighted_content

        next_pos = doc.apply_change(
            start=pos,
            end=end_cmd_pos+len(end_cmd),
            repl=repl,
            category=category
        )

        pos = doc.src.find(begin_cmd, next_pos)


def _process(doc:Document):
    for env in TEX3_SOURCE_CODE_ENVS:
        _process_env_generic(doc, env, Tex3Lexer(), f'env:{env}')


    # inline highlighters
    _process_inline_generic(doc, r'\inltex', Tex3Lexer(), r'\inlinestylea', 'inline:tex3')
    _process_inline_generic(doc, r'\inlpy', Python3Lexer(), r'\inlinestyleb', 'inline:python3')
    _process_inline_generic(doc, r'\inlpl', None, r'\verb', 'inlnie:verbatim', keep_open_close=True)



def _apply_env_safe_line_op(doc:Document, skip_envs:list, op:Callable):
    src = doc.src
    env_cmds = dict()

    for env_name in skip_envs:
        begin_cmd = '\\begin{%s}' % env_name
        end_cmd = '\\end{%s}' % env_name

        env_cmds[env_name] = (begin_cmd, end_cmd)
    
    new_src = ''
    pos = 0

    while pos <= len(src):
        line_end_pos = src.find('\n', pos)
        if line_end_pos == -1:
            line_end_pos = len(src)

        line = src[pos:line_end_pos+1]

        best_env_start_pos = len(src) + 1
        best_env_start_cmd = None
        best_env_end_cmd = None
        for env_name, (env_start, env_end) in env_cmds.items():
            start = line.find(env_start)
            if start != -1 and start < best_env_start_pos:
                best_env_start_pos = start
                best_env_start_cmd = env_start
                best_env_end_cmd = env_end

        # skip comments
        # if no env start is found in this line, apply op and add the result to output
        if best_env_start_cmd is None or doc.is_commented(pos + best_env_start_pos):
            new_src += op(line)
            pos = line_end_pos + 1
            continue

        # an env start command is found in this line, skip all contents until end of the environment
        env_end_pos = pos + best_env_start_pos + len(best_env_start_cmd)
        while True:
            env_end_pos = src.find(best_env_end_cmd, env_end_pos)
            assert env_end_pos != -1
            if not doc.is_commented(env_end_pos):
                break
        
        env_end_pos = src.find('\n', env_end_pos+len(best_env_end_cmd))
        if env_end_pos == -1:
            env_end_pos = len(src)
        
        new_src += src[pos+best_env_start_pos:env_end_pos+1]
        pos = env_end_pos+1

    doc.src = new_src


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
    @click.option('-c', '--clean', help='clean comments', is_flag=True)
    def process(input, output, style, log, protect, clean):
        set_style(style)

        with open(input) as f:
            src = f.read()

        doc = Document(src)
        _process(doc)

        if clean:
            _apply_env_safe_line_op(doc, ['filecontents'], 
                                          lambda x: '' if x.strip().startswith('%') else x)

        if protect:
            _apply_env_safe_line_op(doc, ['filecontents'], 
                                          lambda x: 'PROTECT'.center(80, '%') + '\n' if len(x.strip()) == 0 else x)
        
        src = doc.src
        with open(output, 'w') as f:
            f.write(src)

        if log:
            with open(log, 'w') as f:
                f.write(doc.get_log())

        

    main()

    
    
