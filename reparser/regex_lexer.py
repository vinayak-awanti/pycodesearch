import ply.lex as lex

tokens = (
    'CHAR',
    'OR', 'QUANT', 'DOT',
    'LPAREN', 'RPAREN',
    'CHAR_CLASS'
)


# noinspection PySingleQuotedDocstring,PyPep8Naming
def t_CHAR(t):
    r'[^|+?*\[\]{}()\\.]|\\[|+?*\[\]{}().]|[\n\t\r\v\f]'
    t.value = t.value.strip('\\')
    return t


t_OR = r'\|'
t_QUANT = r'\?|\+|\*|\{\d+\}|\{\d+,\}|\{\d+\,\d+}'
t_DOT = r'\.'
t_LPAREN = r'\('
t_RPAREN = r'\)'
t_CHAR_CLASS = r'\[[^\]]+\]'


def t_error(t):
    print("Illegal character '%s'" % t.value[0])
    t.lexer.skip(1)


lexer = lex.lex()

if __name__ == "__main__":
    lexer.input("[a-zA-Z]")
    while True:
        tok = lexer.token()
        if not tok:
            break
        print(tok)
