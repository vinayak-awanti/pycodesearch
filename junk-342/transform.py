"""
Transform a regex that may represent an infinite language
to a regex that represents a finite language
so as to capture all possible trigrams
"""
import re
import logging
from copy import deepcopy
from json import dumps

from reparser.regex_parser import parse
logging.basicConfig(level="INFO")


def convert(parse_tree: dict):
    if parse_tree["type"] == "repetition":
        modifier_list = ["?"]
        q = "".join(parse_tree["quantifier"].split())
        if q == "*":  # e* -> e?e?
            modifier_list = ["?", "?"]

        elif q == "+":  # e+ -> ee?
            # parse_tree = modify_parse_tree(parse_tree, ["e", "?"])
            modifier_list = ["e", "?"]
            new_node = modify_parse_tree(parse_tree, ["e", "?"])
            parse_tree.clear()
            parse_tree.update(new_node)

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


user_query = "a{9,}"
tree = parse(user_query)
print(dumps(tree, indent=2))
convert(tree)
print(dumps(tree, indent=2))
