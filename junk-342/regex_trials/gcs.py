class RegexQuery:

    ALL = "ALL"
    NONE = "NONE"

    def __init__(self, op, trigram, sub):
        self.op = op
        self.trigram = trigram if trigram else []
        self.sub = sub if sub else []

    def AND(self, other):
        return self.andOr(other, "AND")

    def OR(self, other):
        return self.andOr(other, "OR")

    def andOr(self, other, op):
        r = other
        q = self
        if len(q.trigram) == 0 and len(q.sub) == 1:
            q = q.sub[0]
        if len(r.trigram) == 0 and len(r.sub) == 1:
            r = r.sub[0]

        # Boolean simplification here
        # 282 - 394

    def implies(self, r):
        q = self
        if q.op == "NONE" or r.op == "ALL":
            return True
        if q.op == "ALL" or r.op == "NONE":
            return False
        if q.op == "AND" or (q.op == "OR" and len(q.trigram) == 1 and len(q.sub) == 0)
            return q.trigramImplies(r)
        return q.op == "OR" and r.op == "OR" and q.trigram

class RegexInfo:
    """
    Summarizes the results of analyzing a regexp
    """
    def __init__(self, opts):
        self.emptyable = opts.emptyable if opts.emptyable else False
        self.exact = opts.exact if opts.exact else []
        self.prefix = opts.prefix if opts.prefix else []
        self.suffix = opts.suffix if opts.suffix else []
        self.match = opts.match if opts.match else RegexQuery()

def analyze(re):
    """
    :param re: regular expression
    :return: regexpInfo
    """
    info = RegexInfo()