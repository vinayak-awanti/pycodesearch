import ply.yacc as yacc
from reparser.regex_lexer import tokens

def p_regex(p):
    '''regex : union
             | concat'''
    p[0] = p[1]

def p_union(p):
    '''union : concat OR regex'''
    p[0] = {"type": "union", "value": [p[1], p[3]]}

def p_concat(p):
    '''concat : term concat
              | term'''
    if len(p) == 3:
        # TODO: to be checked thoroughly
        if p[1]["type"] == "literal" and p[2]["type"] == "concat" and p[2]["value"][0]["type"] == "literal":
            p[1]["value"] += p[2]["value"][0]["value"]
            p[2] = p[2]["value"][1] if len(p[2]["value"]) == 2 else None
        p[0] = {"type": "concat", "value": [p[1], p[2]]}
    else:
        p[0] = p[1]

def p_term(p):
    '''term : repetition
            | single_term'''
    p[0] = p[1]

def p_single_term(p):
    '''single_term : literal
                   | wildcard
                   | LPAREN regex RPAREN'''
    if len(p) == 4:
        p[0] = p[2]
    else:
        p[0] = p[1]

def p_repetition(p):
    '''repetition : single_term QUANT'''
    p[0] = {"type": "repetition", "quantifier": p[2], "value": p[1]}

def p_literal(p):
    '''literal : CHAR'''
    p[0] = {"type": "literal", "value": p[1]}

def p_wildcard(p):
    '''wildcard : DOT'''
    p[0] = {"type": "wildcard"}

def p_error(error):
    print("parse error:", error)

def parse(re):
    parser = yacc.yacc()
    return parser.parse(re)
    
if __name__ == "__main__":
    from json import dumps
    while True:
        s = input()
        if s == "quit":
            break
        tree = parse(s)
        print(dumps(tree, indent=2))
