"""
Transform a regex that may represent an infinite language
to a regex that represents a finite language
so as to capture all possible trigrams
"""
import re
from reparser.regex_parser import parse
from copy import deepcopy
from json import dumps

user_query = "((ab)+)+"

tree = parse(user_query)


def convert(parse_tree):
    if parse_tree["type"] == "repetition":
        if parse_tree["quantifier"] == "*":
            child1 = deepcopy(parse_tree)
            child2 = deepcopy(parse_tree)

            child1["quantifier"] = child2["quantifier"] = "?"
            parse_tree["type"] = "concat"
            parse_tree["value"] = [child1, child2]
            del parse_tree["quantifier"]

        elif parse_tree["quantifier"] == "+":
            child1 = deepcopy(parse_tree)
            child2 = deepcopy(parse_tree)

            child1["type"] = child1["value"]["type"]
            child1["value"] = child1["value"]["value"]
            if child1["type"] != "repetition":
                del child1["quantifier"]

            child2["quantifier"] = "?"

            parse_tree["type"] = "concat"
            parse_tree["value"] = [child1, child2]
            del parse_tree["quantifier"]

        # TODO logic for {m}, {m,}, {m,n}
        elif re.fullmatch(r"^{\d+}$", parse_tree["quantifier"]):
            m = int(parse_tree["quantifier"][1:-1])
            times = min(m, 3)

            if times == 0:
                parse_tree["type"] = "literal"
                parse_tree["value"] = ""

            elif times == 1:
                parse_tree["value"] = parse_tree["value"]["value"]
                if parse_tree["type"] != "repetition":
                    del parse_tree["quantifier"]

            elif times == 2:
                parse_tree["type"] = "concat"
                del parse_tree["quantifier"]
                child1 = deepcopy(parse_tree)
                child2 = deepcopy(parse_tree)

                parse_tree["value"] = [child1, child2]

            elif times == 3:
                pass

    if type(parse_tree["value"]) == list:
        for sub_tree in parse_tree["value"]:
            convert(sub_tree)
    elif type(parse_tree["value"]) == dict:
        convert(parse_tree["value"])


print(dumps(tree, indent=2))
convert(tree)
print(dumps(tree, indent=2))
