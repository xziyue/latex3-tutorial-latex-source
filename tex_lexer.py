from pygments.lexer import RegexLexer, DelegatingLexer, include, bygroups, \
    using, this, do_insertions, default, words
from pygments.token import Text, Comment, Operator, Keyword, Name, String, \
    Number, Punctuation, Generic, Other
import re

segments_re = re.compile(r'_+|[a-zA-Z@]+')

def l3_breakdown(content):

    right_segment = []

    left_body = None
    if ':' in content:
        right_segment.append(':')
        left_body, _, spec = content.rpartition(':')
        right_segment.append(spec)
    else:
        left_body = content

    assert left_body.startswith('\\'), f'Invalid L3 command: {content}'

    left_body = left_body[1:]  # Remove leading backslash
    left_segment = ['\\'] + segments_re.findall(left_body)

    return left_segment, right_segment


def find_n_th_letter_index(segment, n):
    count = 0
    for i in range(len(segment)):
        if len(segment[i]) > 0 and (segment[i][0] == '@' or segment[i][0].isalpha()):
            if count == n:
                return i
            count += 1

    return -1  # No letter found

def find_last_letter_index(segment):
    for i in range(len(segment) - 1, -1, -1):
        if len(segment[i]) > 0 and (segment[i][0] == '@' or segment[i][0].isalpha()):
            return i

    return -1  # No letter found


def l3_command_callback(lexer, match):
    left_segment, right_segment = l3_breakdown(match.group(0))
    assert len(right_segment) == 2, f'Invalid L3 command right group: {right_segment}'

    first_index = find_n_th_letter_index(left_segment, 0)

    cur_len = 0

    for i in range(len(left_segment)):
        if i == first_index:
            yield cur_len, Keyword.Namespace, left_segment[i]
        else:
            yield cur_len, Name.Function, left_segment[i]

        cur_len += len(left_segment[i])

    for i in range(len(right_segment)):
        if i == 0:
            yield cur_len, String.Delimiter, right_segment[i]
        else:
            yield cur_len, Name.Attribute, right_segment[i]

        cur_len += len(right_segment[i])

    assert cur_len == len(match.group(0)), f'Length mismatch in L3 command: {match.group(0)}'

def l3_variable_callback(lexer, match):
    left_segment, right_segment = l3_breakdown(match.group(0))
    assert len(right_segment) == 0, f'Invalid L3 variable: {match.group(0)}'

    first_index = find_n_th_letter_index(left_segment, 0)
    second_index = find_n_th_letter_index(left_segment, 1)
    last_index = find_last_letter_index(left_segment)

    index_unique = first_index != second_index and second_index != last_index

    cur_len = 0
    for i in range(len(left_segment)):
        if i == first_index:
            yield cur_len, Name.Class, left_segment[i]
        elif i == second_index and index_unique:
            yield cur_len, Keyword.Namespace, left_segment[i]
        elif i == last_index and index_unique:
            yield cur_len, Keyword.Type, left_segment[i]
        else:
            yield cur_len, Name.Variable, left_segment[i]

        cur_len += len(left_segment[i])

    assert cur_len == len(match.group(0)), f'Length mismatch in L3 variable: {match.group(0)}'

class Tex3Lexer(RegexLexer):
    """
    Lexer for the TeX and LaTeX typesetting languages.
    """

    name = 'TeX'
    aliases = ['tex', 'latex']
    filenames = ['*.tex', '*.aux', '*.toc']
    mimetypes = ['text/x-tex', 'text/x-latex']

    tokens = {
        'general': [
            (r'%.*?\n', Comment),
            (r'[{}]', Name.Builtin),
            (r'[&_^]', Name.Builtin),
        ],
        'root': [
            (r'\\\[', String.Backtick, 'displaymath'),
            (r'\\\(', String, 'inlinemath'),
            (r'\$\$', String.Backtick, 'displaymath'),
            (r'\$', String, 'inlinemath'),
            (r'\\([glc])_{1,2}[a-zA-Z_@]*', l3_variable_callback),
            (r'\\(__)?[a-zA-Z@_]+:[a-zA-Z]*', l3_command_callback),
            (r'\\([a-zA-Z@]+|.)', Name.Function, 'command'),
            (r'\\$', Keyword),
            include('general'),
            (r'[^\\$%&_^{}]+', Text),
        ],
        'math': [
            (r'\\([a-zA-Z]+|.)', Name.Variable),
            include('general'),
            (r'[0-9]+', Number),
            (r'[-=!+*/()\[\]]', Operator),
            (r'[^=!+*/()\[\]\\$%&_^{}0-9-]+', Name.Builtin),
        ],
        'inlinemath': [
            (r'\\\)', String, '#pop'),
            (r'\$', String, '#pop'),
            include('math'),
        ],
        'displaymath': [
            (r'\\\]', String, '#pop'),
            (r'\$\$', String, '#pop'),
            (r'\$', Name.Builtin),
            include('math'),
        ],
        'command': [
            (r'\[.*?\]', Name.Attribute),
            (r'\*', Name.Function),
            default('#pop'),
        ]
    }

    def analyse_text(text):
        for start in ("\\documentclass", "\\input", "\\documentstyle",
                      "\\relax"):
            if text[:len(start)] == start:
                return True


if __name__ == '__main__':

    lexer = Tex3Lexer()

    test_tex = r'''
\tl_put_right:Nn
\l_tmpa_tl
'''.strip()

    for tok in lexer.get_tokens(test_tex):
        print(tok)
