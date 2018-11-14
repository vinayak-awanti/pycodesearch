import logging

from copy import deepcopy

logging.basicConfig(level="INFO")

QNone = 0
QAll = 1
QOr = 2
QAnd = 3

class Query:
    def __init__(self, op, trigram=None, sub=None):
        self.op = op
        self.trigram = [] if trigram == None else trigram
        self.sub = [] if sub == None else sub

    def __str__(self):
        q = self
        if q.op == QNone:
            return "-"
        if q.op == QAll:
            return "+"
        if len(q.sub) == 0 and len(q.trigram) == 1:
            return '"{}"'.format(q.trigram[0])

        s, sjoin, end, tjoin = "", "", "", ""
        if q.op == QAnd:
            sjoin = " "
            tjoin = " "
        else:
            s = "("
            sjoin = ")|("
            end = ")"
            tjoin = "|"
        for i, t in enumerate(q.trigram):
            if i > 0:
                s += tjoin
            s += '"{}"'.format(t)
        if len(q.sub) > 0:
            if len(q.trigram) > 0:
                s += sjoin
            s += q.sub[0].__str__()
            for i in range(1, len(q.sub)):
                s += sjoin + q.sub[i].__str__()
        s += end
        return s

def cross(s, t):
    """
	cross returns the cross product of s and t.
	"""
    p = {}
    p = {x + y for x in s for y in t}
    return p


def union(s, t):
    """
	union returns the union of s and t, reusing s's storage.
	"""
    s = s | t
    return deepcopy(s)


def repeat(s):
    """
	repeat
	"""
    return s | {x + x for x in s}


def analyze(tree):
    if tree == None:
        return set()

    re_type = tree["type"]

    if re_type == "literal":
        return {tree["value"]}

    if re_type == "concat":
        return cross(analyze(tree["value"][0]), analyze(tree["value"][1]))

    if re_type == "union":
        return union(analyze(tree["value"][0]), analyze(tree["value"][1]))

    if re_type == "repetition":
        re_quantifier = tree["quantifier"]
        s = analyze(tree["value"])
        if re_quantifier == '+' or re_quantifier == '*':
            s = repeat(s)
        if re_quantifier == '?' or re_quantifier == '*':
            s.add('')
        return s


def regexp_query(tree):
    string_set = analyze(tree)
    logging.info("analyze identified string set: %s", str(string_set))
    sub = []
    for s in string_set:
        n = len(s)
        if n < 3:
            return Query(QAll)
        tri = []
        for i in range(n - 2):
            tri.append(s[i:i + 3])
        tri = list(set(tri))
        sub += [Query(QAnd, trigram=tri)]
    return Query(QOr, sub=sub)

if __name__ == "__main__":
    from reparser.regex_parser import parse

    tests = [
        (r'Abcdef', '"Abc" "bcd" "cde" "def"'),
        (r'(abc)(def)', '"abc" "bcd" "cde" "def"'),
        (r'abc(def|ghi)', '"abc" ("bcd" "cde" "def")|("bcg" "cgh" "ghi")'),
        (r'a+hello', '"ahe" "ell" "hel" "llo"'),
        (r'(a+hello|b+world)', '("ahe" "ell" "hel" "llo")|("bwo" "orl" "rld" "wor")'),
        (r'a*bbb', '"bbb"'),
        (r'a?bbb', '"bbb"'),
        (r'(bbb)a?', '"bbb"'),
        (r'(bbb)a*', '"bbb"'),
        (r'(abc|bac)de', '"cde" ("abc" "bcd")|("acd" "bac")'),
        (r'(abc|abc)', '"abc"'),
        (r'(ab|ab)c', '"abc"'),
        (r'ab(cab|cat)', '"abc" "bca" ("cab"|"cat")'),
        (r'(z*(abc|def)z*)(z*(abc|def)z*)', '("abc"|"def")'),
        (r'(z*abcz*defz*)|(z*abcz*defz*)', '"abc" "def"'),
        (r'(z*abcz*defz*(ghi|jkl)z*)|(z*abcz*defz*(mno|prs)z*)', '"abc" "def" ("ghi"|"jkl"|"mno"|"prs")'),
        (r'(z*(abcz*def)|(ghiz*jkl)z*)|(z*(mnoz*prs)|(tuvz*wxy)z*)',
         '("abc" "def")|("ghi" "jkl")|("mno" "prs")|("tuv" "wxy")'),
        (r'(z*abcz*defz*)(z*(ghi|jkl)z*)', '"abc" "def" ("ghi"|"jkl")'),
        (r'(z*abcz*defz*)|(z*(ghi|jkl)z*)', '("ghi"|"jkl")|("abc" "def")'),
        (r'(a|ab)cde', '"cde" ("abc" "bcd")|("acd")'),
        (r'(a|b|c|d)(ef|g|hi|j)', '+'),
        (r'abc+def', '"abc" "cde"'),
        (r'abc?def', '"abc" "cde"'),
        (r'ab(cd)*ef', '"abc" "cde"')
    ]

    for test in tests:
        print("test:", test[0])
        tree = parse(test[0])
        print("actual:", regexp_query(tree))
        print("expected:", test[1])

    # while True:
    #     s = input()
    #     if s == "quit":
    #         quit()
    #     tree = parse(s)
    #     q = regexp_query(tree)
    #     print(q)
