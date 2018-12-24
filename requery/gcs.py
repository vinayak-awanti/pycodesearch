from copy import deepcopy
from query import Query, allQuery, noneQuery
from stringset import add, clean, cross, have, minLen, size, union


def regexpQuery(re):
    """
    RegexpQuery returns a Query for the given regexp.
    """
    info = analyze(re)
    info.simplify(True)
    info.addExact()
    return info.match


def analyze(re):
    """
    analyze returns the regexpInfo for the regexp re.
    """
    info = RegexpInfo()
    re_type = re['type']
    if re_type == "NO_MATCH":
        return noMatch()
    elif re_type in {"EMPTY_MATCH", "BEGIN_LINE", "END_LINE", "BEGIN_TEXT", "END_TEXT", "WORD_BOUNDARY",
                     "NO_WORD_BOUNDARY"}:
        return emptyString()
    elif re_type == "literal":
        info.exact = [re['value']]
        info.match = deepcopy(allQuery)
    elif re_type in {"ANY_CHAR_NOT_NL", "ANY_CHAR"}:
        return anyChar()
    elif re_type == "CAPTURE":
        return analyze(re['value'])
    elif re_type == "concat":
        return fold(concat, re['value'], emptyString())
    elif re_type == "union":
        return fold(alternate, re['value'], noMatch())
    elif re_type == "repetition":
        re_quantifier = re['quantifier']
        if re_quantifier == '?':
            return alternate(analyze(re['value']), emptyString())
        elif re_quantifier == '+':
            # x+
            # Since there has to be at least one x, the prefixes and suffixes
            # stay the same.  If x was exact, it isn't anymore.
            info = analyze(re['value'])
            if have(info.exact):
                info.prefix = info.exact
                info.suffix = deepcopy(info.exact)
                info.exact = []
        elif re_quantifier == '*':
            # We don't know anything, so assume the worst.
            return anyMatch()
    elif re_type == "REPEAT":
        try:
            if re['min'] == 0:
                return anyMatch()
        except:
            pass

    info.simplify(False)
    return deepcopy(info)


def fold(f, sub, zero):
    """
    fold is the usual higher-order function.
    """
    if len(sub) == 0:
        return deepcopy(zero)
    elif len(sub) == 1:
        return analyze(sub[0])
    info = f(analyze(sub[0]), analyze(sub[1]))
    for i in range(2, len(sub)):
        info = f(info, analyze(sub[i]))
    return deepcopy(info)


# Exact sets are limited to maxExact strings.
# If they get too big, simplify will rewrite the regexpInfo
# to use prefix and suffix instead.  It's not worthwhile for
# this to be bigger than maxSet.
# Because we allow the maximum length of an exact string
# to grow to 5 below (see simplify), it helps to avoid ridiculous
# alternations if maxExact is sized so that 3 case-insensitive letters
# triggers a flush.
maxExact = 7

# Prefix and suffix sets are limited to maxSet strings.
# If they get too big, simplify will replace groups of strings
# sharing a common leading prefix (or trailing suffix) with
# that common prefix (or suffix).  It is useful for maxSet
# to be at least 2³ = 8 so that we can exactly
# represent a case-insensitive abc by the set
# {abc, abC, aBc, aBC, Abc, AbC, ABc, ABC}.
maxSet = 20


class RegexpInfo(object):
    """
    A regexpInfo summarizes the results of analyzing a regexp.
    """

    def __init__(self, canEmpty=False, exact=None, prefix=None, suffix=None, match=None):
        self.canEmpty = canEmpty
        self.exact = [] if exact is None else exact
        self.prefix = [] if prefix is None else prefix
        self.suffix = [] if suffix is None else suffix
        self.match = match

    def addExact(self):
        """
        addExact adds to the match query the trigrams for matching info.exact.
        """
        if have(self.exact):
            self.match = self.match.andTrigrams(self.exact)

    def simplify(self, force):
        """
        simplify simplifies the regexpInfo when the exact set gets too large.
        """
        # print(" simplify", self, " force=", force)
        # If there are now too many exact strings,
        # loop over them, adding trigrams and moving
        # the relevant pieces into prefix and suffix.
        clean(self.exact, False)
        if len(self.exact) > maxExact or (minLen(self.exact) >= 3 and force) or (minLen(self.exact) >= 4):
            self.addExact()
            for s in self.exact:
                n = len(s)
                if n < 3:
                    add(self.prefix, s)
                    add(self.suffix, s)
                else:
                    add(self.prefix, s[:2])
                    add(self.suffix, s[n - 2:])
            self.exact = []

        if not have(self.exact):
            self.simplifySet(self.prefix, False)
            self.simplifySet(self.suffix, True)

    def simplifySet(self, s, isSuffix):
        """
        simplifySet reduces the size of the given set (either prefix or suffix).
        There is no need to pass around enormous prefix or suffix sets, since
        they will only be used to create trigrams.  As they get too big, simplifySet
        moves the information they contain into the match query, which is
        more efficient to pass around.
        """
        t = s
        clean(t, isSuffix)

        # Add the OR of the current prefix/suffix set to the query.
        self.match = self.match.andTrigrams(t)
        n = 3
        while n == 3 or size(t) > maxSet:
            # Replace set by strings of length n-1.
            w = 0
            for st in t:
                if len(st) >= n:
                    if not isSuffix:
                        st = st[:n - 1]
                    else:
                        st = st[len(st) - n + 1:]
                if w == 0 or t[w - 1] != st:
                    t[w] = st
                    w += 1
            t = t[:w]
            clean(t, isSuffix)
            n -= 1

        # Now make sure that the prefix/suffix sets aren't redundant.
        # For example, if we know "ab" is a possible prefix, then it
        # doesn't help at all to know that  "abc" is also a possible
        # prefix, so delete "abc".
        w = 0
        f = str.endswith if isSuffix else str.startswith
        for st in t:
            if w == 0 or not f(st, t[w - 1]):
                t[w] = st
                w += 1
        t = t[:w]

        s[:] = t

    def __str__(self):
        s = ''
        if self.canEmpty:
            s += "canempty "
        if have(self.exact):
            s += "exact: " + ",".join(self.exact)
        else:
            s += "prefix: " + ','.join(self.prefix)
            s += " suffix:" + ','.join(self.suffix)
        s += " match: " + str(self.match)
        return s


def anyMatch():
    """
    anyMatch returns the regexpInfo describing a regexp that
    matches any string.
    """
    return RegexpInfo(
        canEmpty=True,
        prefix=[''],
        suffix=[''],
        match=deepcopy(allQuery)
    )


def anyChar():
    """
    anyChar returns the regexpInfo describing a regexp that
    matches any single character.
    """
    return RegexpInfo(
        prefix=[''],
        suffix=[''],
        match=deepcopy(allQuery)
    )


def noMatch():
    """
    noMatch returns the regexpInfo describing a regexp that
    matches no strings at all.
    """
    return RegexpInfo(
        match=deepcopy(noneQuery)
    )


def emptyString():
    """
    emptyString returns the regexpInfo describing a regexp that
    matches only the empty string.
    """
    return RegexpInfo(
        canEmpty=True,
        exact=[''],
        match=deepcopy(allQuery)
    )


def concat(x, y):
    """
    concat returns the regexp info for xy given x and y.
    """
    # print("concat", x, "...", y)
    xy = RegexpInfo()
    xy.match = x.match.q_and(y.match)
    if have(x.exact) and have(y.exact):
        xy.exact = cross(x.exact, y.exact, False)
    else:
        if have(x.exact):
            xy.prefix = cross(x.exact, y.prefix, False)
        else:
            xy.prefix = x.prefix
            if x.canEmpty:
                xy.prefix = union(xy.prefix, y.prefix, False)
        if have(y.exact):
            xy.suffix = cross(x.suffix, y.exact, True)
        else:
            xy.suffix = y.suffix
            if y.canEmpty:
                xy.suffix = union(xy.suffix, x.suffix, True)

    # If all the possible strings in the cross product of x.suffix
    # and y.prefix are long enough, then the trigram for one
    # of them must be present and would not necessarily be
    # accounted for in xy.prefix or xy.suffix yet.  Cut things off
    # at maxSet just to keep the sets manageable.
    if (not have(x.exact) and not have(y.exact) and size(x.suffix) <= maxSet and size(y.prefix) <= maxSet and minLen(
            x.suffix) + minLen(y.prefix) >= 3):
        xy.match = xy.match.andTrigrams(cross(x.suffix, y.prefix, False))

    xy.simplify(False)
    return deepcopy(xy)


def alternate(x, y):
    """
    alternate returns the regexpInfo for x|y given x and y.
    """
    # print("alternate", x, "...", y)
    xy = RegexpInfo()
    if have(x.exact) and have(y.exact):
        xy.exact = union(x.exact, y.exact, False)
    elif have(x.exact):
        xy.prefix = union(x.exact, y.prefix, False)
        xy.suffix = union(x.exact, y.suffix, True)
        x.addExact()
    elif have(y.exact):
        xy.prefix = union(x.prefix, y.exact, False)
        xy.suffix = union(x.suffix, deepcopy(y.exact), True)
        y.addExact()
    else:
        xy.prefix = union(x.prefix, y.prefix, False)
        xy.suffix = union(x.suffix, y.suffix, True)
    xy.canEmpty = x.canEmpty or y.canEmpty
    xy.match = x.match.q_or(y.match)

    xy.simplify(False)
    return deepcopy(xy)


if __name__ == "__main__":
    from reparser import regex_parser

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
        (r'(a|b|c|d)(ef|g|hi|j)', '+')
    ]

    for test in tests:
        print("test:", test[0])
        tree = regex_parser.parse(test[0])
        # print(dumps(tree, indent=2))
        matched = regexpQuery(tree)
        print("actual:", matched)
        print("expected:", test[1])
