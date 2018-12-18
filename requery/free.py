import logging
from query import allQuery
from copy import deepcopy
from reparser.regex_parser import parse

def cross(s, t):
    return {x + y for x in s for y in t}


def analyze(tree):
    if tree is None:
        return []

    re_type = tree["type"]

    if re_type == "literal":
        return {tree["value"]}

    if re_type == "concat":
        return cross(analyze(tree["value"][0]), analyze(tree["value"][1]))

    if re_type == "union":
        return analyze(tree["value"][0]) | analyze(tree["value"][1])

    if re_type == "repetition":
        return {""}


def analyze2(tree):
    if tree is None:
        return []

    re_type = tree["type"]

    if re_type == "literal":
        return tree["value"]

    if re_type == "concat":
        return {"AND": [analyze2(tree["value"][0]), analyze2(tree["value"][1])]}

    if re_type == "union":
        return {"OR": [analyze2(tree["value"][0]), analyze2(tree["value"][1])]}

    if re_type == "repetition":
        return {}


def freeQuery(tree):
    string_set = analyze(tree)
    logging.info("analyze identified string set: %s", str(string_set))
    q = deepcopy(allQuery)
    return q.andTrigrams(list(string_set))


if __name__ == "__main__":
    #TODO make these tests work!
    tests = [
        (r"(abcd|efgh)(ijklm|x*)", '("abc" "bcd")|("efg" "fgh")'),
        (r"(abc|cba)def", '("abc" | "cba") "def"'),
        (r"abc+de", "+"),
        (r"(abc*)+de", "+"),
        (r"ab(cd)*ef", "+"),
        (r"abc|def", '("abc" | "cba")')
    ]

    for test in tests:
        print("test:", test[0])
        parse_tree = parse(test[0])
        print("tree:", parse_tree)
        print("analyze2:", analyze2(tree=parse_tree))
        print("actual:", freeQuery(parse_tree))
        print("expected:", test[1])
