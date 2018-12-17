from copy import deepcopy

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
