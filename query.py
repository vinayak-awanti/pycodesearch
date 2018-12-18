from copy import deepcopy
from stringset import clean, isSubsetOf, union


class Query:
    """
    A Query is a matching machine, like a regular expression,
    that matches some text and not other text.  When we compute a
    Query from a regexp, the Query is a conservative version of the
    regexp: it matches everything the regexp would match, and probably
    quite a bit more.  We can then filter target files by whether they match
    the Query (using a trigram index) before running the comparatively
    more expensive regexp machinery.
    """
    QAll = 0  # Everything matches
    QNone = 1  # Nothing matches
    QAnd = 2  # All in Sub and Trigram must match
    QOr = 3  # At least one in Sub or Trigram must match

    def __init__(self, o, trigram=None, sub=None):
        self.op = o
        self.trigram = [] if trigram is None else trigram
        self.sub = [] if sub is None else sub

    def q_and(self, r):
        """
        and returns the query q AND r, possibly reusing q's and r's storage.  
        q_and equivalent to "and" in regexp.go, and is a keyword in python.
        """
        return self.andOr(r, Query.QAnd)

    def q_or(self, r):
        """
        or returns the query q OR r, possibly reusing q's and r's storage.
        q_or equivalent to "or" in regexp.go, or is a keyword in python.
        """
        return self.andOr(r, Query.QOr)

    def andOr(self, r, op):
        """
        andOr returns the query q AND r or q OR r, possibly reusing q's and r's storage.
        It works hard to avoid creating unnecessarily complicated structures.
        """
        q = self
        # opstr is for debugging I guess.
        opstr = "&"
        if op == Query.QOr:
            opstr = "|"
        # print("andOr", q, opstr, r)
        _ = opstr

        if len(q.trigram) == 0 and len(q.sub) == 1:
            q = q.sub[0]
        if len(r.trigram) == 0 and len(r.sub) == 1:
            r = r.sub[0]

        # Boolean simplification
        # If q ⇒ r, q AND r ≡ q.
        # If q ⇒ r, q OR r ≡ r.
        if q.implies(r):
            # print(q, "implies", r)
            if op == Query.QAnd:
                return deepcopy(q)
            return deepcopy(r)
        if r.implies(q):
            # print(r, "implies", q)
            if op == Query.QAnd:
                return deepcopy(r)
            return deepcopy(q)

        # Both q and r are QAnd or Qor.
        # If they match or can be made to match, merge.
        qAtom = len(q.trigram) == 1 and len(q.sub) == 0
        rAtom = len(r.trigram) == 1 and len(r.sub) == 0
        if q.op == op and (r.op == op or rAtom):
            q.trigram = union(q.trigram, r.trigram, False)
            q.sub.extend(r.sub)
            return deepcopy(q)
        if r.op == op and qAtom:
            r.trigram = union(r.trigram, q.trigram, False)
            return deepcopy(r)
        if qAtom and rAtom:
            q.op = op
            q.trigram.extend(r.trigram)
            return deepcopy(q)

        # If one matches the op, add the other to it.
        if q.op == op:
            q.sub.append(r)
            return deepcopy(q)
        if r.op == op:
            r.sub.append(q)
            return deepcopy(r)

        # We are creating an AND of ORs or an OR of ANDs.
        # Factor out common trigrams, if any.
        qs = set(q.trigram)
        rs = set(r.trigram)
        common = qs & rs
        q.trigram = list(qs - common)
        r.trigram = list(rs - common)
        common = list(common)

        if len(common) > 0:
            # If there were common trigrams, rewrite
            #
            #    (abc|def|ghi|jkl) AND (abc|def|mno|prs) =>
            #        (abc|def) OR ((ghi|jkl) AND (mno|prs))
            #
            #    (abc&def&ghi&jkl) OR (abc&def&mno&prs) =>
            #        (abc&def) AND ((ghi&jkl) OR (mno&prs))
            #
            # Build up the right one of
            #    (ghi|jkl) AND (mno|prs)
            #    (ghi&jkl) OR (mno&prs)
            # Call andOr recursively in case q and r can now be simplified
            # (we removed some trigrams).
            s = q.andOr(r, op)

            # Add in factored trigrams.
            otherOp = Query.QAnd + Query.QOr - op
            t = Query(otherOp, common)
            return t.andOr(s, t.op)

        # Otherwise just create the op.
        return Query(op, sub=[deepcopy(q), deepcopy(r)])

    def implies(self, r):
        """
        implies reports whether q implies r.
        It is okay for it to return false negatives.
        """
        q = self
        if q.op == Query.QNone or r.op == Query.QAll:
            # False implies everything.
            # Everything implies True.
            return True
        if q.op == Query.QAll or r.op == Query.QNone:
            # True implies nothing.
            # Nothing implies False
            return False
        if q.op == Query.QAnd or (q.op == Query.QOr and len(q.trigram) == 1 and len(q.sub) == 0):
            return trigramsImply(q.trigram, r)

        if q.op == Query.QOr and r.op == Query.QOr and len(q.trigram) > 0 and len(q.sub) == 0 and isSubsetOf(q.trigram,
                                                                                                             r.trigram):
            return True
        return False

    def maybeRewrite(self, op):
        """
        maybeRewrite rewrites q to use op if it is possible to do so
        without changing the meaning.  It also simplifies if the node
        """
        q = self
        if q.op != Query.QAnd and q.op != Query.QOr:
            return

        n = len(q.sub) + len(q.trigram)

        # AND/OR doing real work?  Can't rewrite.
        if n > 1:
            return

        # Nothing left in the AND/OR?
        if n == 0:
            if q.op == Query.QAnd:
                q.op = Query.QAll
            else:
                q.op = Query.QNone
            return

        # Just a sub-node: throw away wrapper.
        if len(q.sub) == 1:
            q = q.sub[0]

        # Just a trigram: can use either op.
        q.op = op

    def andTrigrams(self, t):
        """
        andTrigrams returns q AND the OR of the AND of the trigrams present in each string.
        """
        q = self
        # If there is a short string, we can't guarantee
        # that any trigrams must be present, so use ALL.
        # q AND ALL = q.
        if len(t) == 0 or min(len(x) for x in t) < 3:
            return deepcopy(q)

        # print("andTrigrams", t)
        q_or = deepcopy(noneQuery)
        for tt in t:
            trig = []
            for i in range(0, len(tt) - 2):
                trig.append(tt[i:i + 3])
            clean(trig, False)
            # print(tt, "trig", trig)
            q_or = q_or.q_or(Query(Query.QAnd, trig))
        q = q.q_and(q_or)
        return deepcopy(q)

    def __str__(self):
        # not applicable in python
        # if q == nil {
        #     return "?"
        # }
        q = self
        if q.op == Query.QNone:
            return "-"
        if q.op == Query.QAll:
            return "+"
        if len(q.sub) == 0 and len(q.trigram) == 1:
            return '"{}"'.format(q.trigram[0])

        s, sjoin, end, tjoin = "", "", "", ""
        if q.op == Query.QAnd:
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


def trigramsImply(t, q):
    if q.op == Query.QOr:
        for qq in q.sub:
            if trigramsImply(t, qq):
                return True
        for i in range(len(t)):
            if isSubsetOf([t[i]], q.trigram):
                return True
        return False
    elif q.op == Query.QAnd:
        for qq in q.sub:
            if not trigramsImply(t, qq):
                return False
        if not isSubsetOf(q.trigram, t):
            return False
        return True
    return False


allQuery = Query(Query.QAll)
noneQuery = Query(Query.QNone)
