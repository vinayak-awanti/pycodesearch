from ply.lex import lex
from ply.yacc import yacc

tokens = ("ALTERNATE", "PLUS", "STAR", "QUESTION", "CHAR")

t_ALTERNATE = r"\|"
t_PLUS = r"\+"
t_STAR = r"\*"
t_QUESTION = r"\?"
t_CHAR = r"\w"

def p_expression(t):
    '''expression : ( expression )
                  | expression expression
                  | expression ALTERNATE expression
                  | expression PLUS
                  | expression STAR
                  | expression QUESTION
                  | CHAR
                  | "" '''
