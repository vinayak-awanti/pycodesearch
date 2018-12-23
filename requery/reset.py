import re
import logging
from copy import deepcopy
from query import allQuery
from reparser.regex_parser import parse
from query import Query, allQuery

def cross(s, t):
    return {x + y for x in s for y in t}


def repeat(s):
    return s | {x + x for x in s}


def convert(parse_tree: dict):
    if parse_tree["type"] == "repetition":
        modifier_list = ["?"]
        q = "".join(parse_tree["quantifier"].split())
        if q == "*":  # e* -> e?e?
            modifier_list = ["?", "?"]

        elif q == "+":  # e+ -> ee?
            # parse_tree = modify_parse_tree(parse_tree, ["e", "?"])
            modifier_list = ["e", "?"]

        elif re.fullmatch(r"^{\d+}$", q):  # e{m} -> e * min(m,3)
            m, = map(int, re.findall(r"\d+", q))
            modifier_list = ["e"]*min(m, 3)

        elif re.fullmatch(r"^{\d+,}$", q):
            m, = map(int, re.findall(r"\d+", q))
            modifier_list = ["e"]*min(m, 3) + ["?"]*max(0, 3-m)

        elif re.fullmatch(r"^{\d+,\d+}$", q):
            m, n = map(int, re.findall(r"\d+", q))
            modifier_list = ["e"] * min(m, 3) + ["?"] * min(n-m, 3-min(m, 3))

        new_node = modify_parse_tree(parse_tree, modifier_list)
        parse_tree.clear()
        parse_tree.update(new_node)

    elif parse_tree["type"] == "char_class":
        parse_tree["type"] = "literal"
        parse_tree["value"] = "ω"

    if type(parse_tree["value"]) == list:
        for sub_tree in parse_tree["value"]:
            convert(sub_tree)
    elif type(parse_tree["value"]) == dict:
        convert(parse_tree["value"])


def modify_parse_tree(root: dict, modifier_list: list) -> dict:
    """
    Recursively modifies the parse tree based on the list.
    modifier_list = ['e', 'e', '?'] if the expression e at root should be modified
    to {concat : {e, concat: {e, {repetition: '?', value: e}}}}
    :param root: root node of the parse tree
    :param modifier_list: list with instructions
    :return: new root
    """
    assert modifier_list
    if len(modifier_list) == 1:
        if modifier_list[0] == "?":
            return {
                "type": "repetition",
                "quantifier": "?",
                "value": deepcopy(root["value"])
            }
        else:
            return deepcopy(root["value"])
    else:
        return {
            "type": "concat",
            "value": [
                modify_parse_tree(root, modifier_list[:1]),
                modify_parse_tree(root, modifier_list[1:])
            ]
        }


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
    convert(tree)
    string_set = analyze(tree)
    logging.info("analyze identified string set: %s", str(string_set))
    sub = []
    for tt in string_set:
        trig = []
        for i in range(0, len(tt) - 2):
            if 'ω' not in tt[i:i + 3]:
                trig.append(tt[i:i + 3])
        sub.append(Query(Query.QAnd, trig))
    return Query(Query.QOr, sub=sub)


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
        print("actual:", regexp_query(parse(test[0])))
        print("expected:", test[1])

    # while True:
    #     s = input()
    #     if s == "quit":
    #         quit()
    #     tree = parse(s)
    #     q = regexp_query(tree)
    #     print(q)
