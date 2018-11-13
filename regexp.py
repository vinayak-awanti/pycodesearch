import sys
from copy import deepcopy

QAll = 0 # Everything matches
QNone = 1 # Nothing matches
QAnd = 2 # All in Sub and Trigram must match
QOr = 3 # At least one in Sub or Trigram must match

sys.setrecursionlimit(100)

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
	def __init__(self, Op, Trigram=None, Sub=None):
		self.Op = Op
		self.Trigram = [] if Trigram is None else Trigram
		self.Sub = [] if Sub is None else Sub

	def q_and(self, r):
		"""
		and returns the query q AND r, possibly reusing q's and r's storage.  
		q_and equivalent to "and" in regexp.go, and is a keyword in python.
		"""
		return self.andOr(r, QAnd)

	def q_or(self, r):
		"""
		or returns the query q OR r, possibly reusing q's and r's storage.
		q_or equivalent to "or" in regexp.go, or is a keyword in python.
		"""
		return self.andOr(r, QOr)
    
	def andOr(self, r, op):
		"""
		andOr returns the query q AND r or q OR r, possibly reusing q's and r's storage.
		It works hard to avoid creating unnecessarily complicated structures.
		"""
		q = self
		# opstr is for debugging I guess.
		opstr = "&"
		if op == QOr:
			opstr = "|"
		# print("andOr", q, opstr, r)
		_ = opstr

		if len(q.Trigram) == 0 and len(q.Sub) == 1:
			q = q.Sub[0]
		if len(r.Trigram) == 0 and len(r.Sub) == 1:
			r = r.Sub[0]
		
		# Boolean simplification
		# If q ⇒ r, q AND r ≡ q.
		# If q ⇒ r, q OR r ≡ r.
		if q.implies(r):
			# print(q, "implies", r)
			if op == QAnd:
				return deepcopy(q)
			return deepcopy(r)
		if r.implies(q):
			# print(r, "implies", q)
			if op == QAnd:
				return deepcopy(r)
			return deepcopy(q)
		
		# Both q and r are QAnd or Qor.
		# If they match or can be made to match, merge.
		qAtom = len(q.Trigram) == 1 and len(q.Sub) == 0
		rAtom = len(r.Trigram) == 1 and len(r.Sub) == 0
		if q.Op == op and (r.Op == op or rAtom):
			q.Trigram = union(q.Trigram, r.Trigram, False)
			q.Sub.extend(r.Sub)
			return deepcopy(q)
		if r.Op == op and qAtom:
			r.Trigram = union(r.Trigram, q.Trigram, False)
			return deepcopy(r)
		if qAtom and rAtom:
			q.Op = op
			q.Trigram.extend(r.Trigram)
			return deepcopy(q)

		# If one matches the op, add the other to it.
		if q.Op == op:
			q.Sub.append(r)
			return deepcopy(q)
		if r.Op == op:
			r.Sub.append(q)
			return deepcopy(r)
		
		# We are creating an AND of ORs or an OR of ANDs.
		# Factor out common trigrams, if any.
		qs = set(q.Trigram)
		rs = set(r.Trigram)
		common = qs & rs
		q.Trigram = list(qs - common)
		r.Trigram = list(rs - common)
		common = list(common)
		
		# TODO: check if sort is necessary
		# q.Trigram.sort()
		# r.Trigram.sort()
		
		if len(common) > 0:
			# If there were common trigrams, rewrite
			#
			#	(abc|def|ghi|jkl) AND (abc|def|mno|prs) =>
			#		(abc|def) OR ((ghi|jkl) AND (mno|prs))
			#
			#	(abc&def&ghi&jkl) OR (abc&def&mno&prs) =>
			#		(abc&def) AND ((ghi&jkl) OR (mno&prs))
			#
			# Build up the right one of
			#	(ghi|jkl) AND (mno|prs)
			#	(ghi&jkl) OR (mno&prs)
			# Call andOr recursively in case q and r can now be simplified
			# (we removed some trigrams).
			s = q.andOr(r, op)

			# Add in factored trigrams.
			otherOp = QAnd + QOr - op
			t = Query(otherOp, common)
			return t.andOr(s, t.Op)

		# Otherwise just create the op.
		return Query(op, Sub=[deepcopy(q), deepcopy(r)])
    
	def implies(self, r):
		"""
		implies reports whether q implies r.
		It is okay for it to return false negatives.
		"""
		q = self
		if q.Op == QNone or r.Op == QAll:
			# False implies everything.
			# Everything implies True.
			return True
		if q.Op == QAll or r.Op == QNone:
			# True implies nothing.
			# Nothing implies False
			return False
		if q.Op == QAnd or (q.Op == QOr and len(q.Trigram) == 1 and len(q.Sub) == 0):
			return trigramsImply(q.Trigram, r)
		
		if q.Op == QOr and r.Op == QOr and len(q.Trigram) > 0 and len(q.Sub) == 0 and isSubsetOf(q.Trigram, r.Trigram):
			return True
		return False

	def maybeRewrite(self, op):
		"""
		maybeRewrite rewrites q to use op if it is possible to do so
		without changing the meaning.  It also simplifies if the node
		"""
		q = self
		if q.Op != QAnd and q.Op != QOr:
			return

		n = len(q.Sub) + len(q.Trigram)

		# AND/OR doing real work?  Can't rewrite.
		if n > 1:
			return

		# Nothing left in the AND/OR?
		if n == 0:
			if q.Op == QAnd:
				q.Op = QAll
			else:
				q.Op = QNone
			return
		
		# Just a sub-node: throw away wrapper.
		if len(q.Sub) == 1:
			q = q.Sub[0]

		# Just a trigram: can use either op.
		q.Op = op
    
	def andTrigrams(self, t):
		"""
		andTrigrams returns q AND the OR of the AND of the trigrams present in each string.
		"""
		q = self
		# If there is a short string, we can't guarantee
		# that any trigrams must be present, so use ALL.
		# q AND ALL = q.
		if minLen(t) < 3:
			return deepcopy(q)

		# print("andTrigrams", t)
		q_or = deepcopy(noneQuery)
		for tt in t:
			trig = []
			for i in range(0, len(tt) - 2):
				add(trig, tt[i:i+3])
			clean(trig, False)
			# print(tt, "trig", trig)
			q_or = q_or.q_or(Query(QAnd, trig))
		q = q.q_and(q_or)
		return deepcopy(q)

	def __str__(self):
		# not applicable in python
		# if q == nil {
		#     return "?"
		# }
		q = self
		if q.Op == QNone:
			return "-"
		if q.Op == QAll:
			return "+"
		if len(q.Sub) == 0 and len(q.Trigram) == 1:
			return '"{}"'.format(q.Trigram[0])
		
		s, sjoin, end, tjoin = "", "", "", ""
		if q.Op == QAnd:
			sjoin = " "
			tjoin = " "
		else:
			s = "("
			sjoin = ")|("
			end = ")"
			tjoin = "|"
		for i, t in enumerate(q.Trigram):
			if i > 0:
				s += tjoin
			s += '"{}"'.format(t)
		if len(q.Sub) > 0:
			if len(q.Trigram) > 0:
				s += sjoin
			s += q.Sub[0].__str__()
			for i in range(1, len(q.Sub)):
				s += sjoin + q.Sub[i].__str__()
		s += end
		return s

def trigramsImply(t, q):
	if q.Op == QOr:
		for qq in q.Sub:
			if trigramsImply(t, qq):
				return True
		for i in range(len(t)):
			if isSubsetOf([t[i]], q.Trigram):
				return True
		return False
	elif q.Op == QAnd:
		for qq in q.Sub:
			if not trigramsImply(t, qq):
				return False
		if not isSubsetOf(q.Trigram, t):
			return False
		return True
	return False

def regexpQuery(re):
	"""
	RegexpQuery returns a Query for the given regexp.
	"""
	info = analyze(re)
	info.simplify(True)
	info.addExact()
	return info.match

allQuery = Query(QAll)
noneQuery = Query(QNone)

def analyze(re):
	"""
	analyze returns the regexpInfo for the regexp re.
	"""
	info = RegexpInfo()
	re_type = re['type']
	if re_type == "NO_MATCH":
		return noMatch()
	elif re_type in {"EMPTY_MATCH", "BEGIN_LINE", "END_LINE", "BEGIN_TEXT", "END_TEXT", "WORD_BOUNDARY", "NO_WORD_BOUNDARY"}:
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
				info.suffix = copy(info.exact)
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
	# print("analyze:", info)
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
	# print("fold:", info)
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
	def __init__(self, canEmpty=False, exact=None, prefix=None, suffix=None, match = None):
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
			for i in range(len(self.exact)):
				s = self.exact[i]
				n = len(s)
				if n < 3:
					add(self.prefix, s)
					add(self.suffix, s)
				else:
					add(self.prefix, s[:2])
					add(self.suffix, s[n-2:])
			self.exact = []

		if not have(self.exact):
			self.simplifySet(self.prefix, False)
			self.simplifySet(self.suffix, True)
		# print("break here")

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
		while(n == 3 or size(t) > maxSet):
			# Replace set by strings of length n-1.
			w = 0
			for st in t:
				if(len(st) >= n):
					if not isSuffix:
						st = st[:n-1]
					else:
						st = st[len(st) - n + 1:]
				if w == 0 or t[w-1] != st:
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
			if w == 0 or f(st, t[w-1]):
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
	if(have(x.exact) and have(y.exact)):
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
	if (not have(x.exact) and not have(y.exact) and size(x.suffix) <= maxSet and size(y.prefix) <= maxSet and minLen(x.suffix) + minLen(y.prefix) >= 3): 
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
		xy.suffix = union(x.suffix, copy(y.exact), True)
		y.addExact()
	else:
		xy.prefix = union(x.prefix, y.prefix, False)
		xy.suffix = union(x.suffix, y.suffix, True)
	xy.canEmpty = x.canEmpty or y.canEmpty
	xy.match = x.match.q_or(y.match)

	xy.simplify(False)
	return deepcopy(xy)

# A stringSet is a set of strings.
# The nil stringSet indicates not having a set.
# The non-nil but empty stringSet is the empty set.

def have(s):
	"""
	have reports whether we have a stringSet.
	"""
	return len(s) > 0

# not used anywhere
def contains(s, string):
	"""
	contains reports whether s contains str.
	"""
	return (string in s)

def add(s, string):
	"""
	add adds str to the set.
	"""
	s.append(string)

def clean(s, isSuffix):
	"""
	clean removes duplicates from the stringSet.
	"""
	if isSuffix:
		s.sort(key = lambda x: x[::-1])
	else:
		s.sort()
	w = 0
	for st in s:
		if(w == 0 or s[w-1] != st):
			s[w] = st
			w += 1
	s[:] = s[:w]

def size(s):
	return len(s)

def minLen(s):
	"""
	minLen returns the length of the shortest string in s.
	"""
	if len(s) == 0:
		return 0
	x = len(s[0])
	for st in s:
		x = min(x, len(st))
	return x

# not used anywhere
def maxLen(s):
	"""
	maxLen returns the length of the longest string in s.
	"""
	if len(s) == 0:
		return 0
	x = len(s[0])
	for st in s:
		x = max(x, len(st))
	return x

def union(s, t, isSuffix):
	"""
	union returns the union of s and t, reusing s's storage.
	"""
	s = s + t
	clean(s, isSuffix)
	return deepcopy(s)

def cross(s, t, isSuffix):
	"""
	cross returns the cross product of s and t.
	"""
	p = []
	p = [x + y for x in s for y in t] 
	clean(p, isSuffix)
	return p

def clear(s):
	"""
	clear empties the set but preserves the storage.
	"""
	s[:] = []

def	copy(s):
	"""
	copy returns a copy of the set that does not share storage with the original.
	"""
	return s[:]

def isSubsetOf(s, t):
	"""
	isSubsetOf returns true if all strings in s are also in t.
	It assumes both sets are sorted.
	"""
	return set(s).issubset(set(t))

if __name__ == "__main__":
	from reparser import regex_parser
	from json import dumps
	tests = [
		(r'Abcdef', '"Abc" "bcd" "cde" "def"'),
		(r'(abc)(def)', '"abc" "bcd" "cde" "def"'),
		(r'abc(def|ghi)','"abc" ("bcd" "cde" "def")|("bcg" "cgh" "ghi")'),
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
		(r'(a|b|c|d)(ef|g|hi|j)', '+')
	]

	for test in tests:
		print("test:", test[0])
		tree = regex_parser.parse(test[0])
		# print(dumps(tree, indent=2))
		match = regexpQuery(tree)
		print("actual:", match)
		print("expected:", test[1])