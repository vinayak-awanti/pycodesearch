import logging
from copy import deepcopy
from query import allQuery
from reparser.regex_parser import parse


def cross(s, t):
    return {x + y for x in s for y in t}


def repeat(s):
    return s | {x + x for x in s}


def analyze(tree):
    if tree is None:
        return set()

    re_type = tree["type"]

    if re_type == "literal":
        return {tree["value"]}

    if re_type == "concat":
        return cross(analyze(tree["value"][0]), analyze(tree["value"][1]))

    if re_type == "union":
        return analyze(tree["value"][0]) | analyze(tree["value"][1])

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
    q = deepcopy(allQuery)
    return q.andTrigrams(list(string_set))


if __name__ == "__main__":

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
        (r'(z*(abcz*def)|(ghiz*jkl)z*)|(z*(mnoz*prs)|(tuvz*wxy)z*)', '("abc" "def")|("ghi" "jkl")|("mno" "prs")|("tuv" "wxy")'),
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
        parse_tree = parse(test[0])
        print("actual:", regexp_query(parse_tree))
        print("expected:", test[1])

    # while True:
    #     s = input()
    #     if s == "quit":
    #         quit()
    #     tree = parse(s)
    #     q = regexp_query(tree)
    #     print(q)
