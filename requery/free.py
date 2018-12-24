from copy import deepcopy
from reparser.regex_parser import parse
from query import Query, allQuery


def cross(s, t):
    return {x + y for x in s for y in t}


def get_trigrams(raw_str):
    prev = raw_str[:3]
    if len(prev) == 3:
        yield prev
    for j in range(3, len(raw_str)):
        prev = prev[1:] + raw_str[j]
        yield prev


# print(list(get_trigrams("ab")))


def freeQuery(tree):
    # if tree is None:
    #     return []

    re_type = tree["type"]
    if re_type == "literal":
        trigram_list = list(get_trigrams(tree["value"]))

        if len(trigram_list):
            return Query(o=Query.QAnd, trigram=trigram_list)
        else:
            return deepcopy(allQuery)

    if re_type == "concat":
        q = freeQuery(tree["value"][0])
        r = freeQuery(tree["value"][1])
        return q.andOr(r, Query.QAnd)
        # return {"AND": [freeQuery(tree["value"][0]), freeQuery(tree["value"][1])]}

    if re_type == "union":
        q = freeQuery(tree["value"][0])
        r = freeQuery(tree["value"][1])
        return q.andOr(r, Query.QOr)
        # return {"OR": [freeQuery(tree["value"][0]), freeQuery(tree["value"][1])]}

    if re_type == "repetition":
        return deepcopy(allQuery)


if __name__ == "__main__":
    tests = [
        (r"(abcd|efgh)(ijklm|x*)", '("abc" "bcd")|("efg" "fgh")'),
        (r"(abc|cba)def", '("abc" | "cba") "def"'),
        (r"abc+de", "+"),
        (r"(abc*)+de", "+"),
        (r"ab(cd)*ef", "+"),
        (r"abc|def", '("abc" | "def")')
    ]

    for test in tests:
        print("test:", test[0])
        parse_tree = parse(test[0])
        # print("tree:", parse_tree)
        print("actual:", freeQuery(tree=parse_tree))
        print("expected:", test[1])
