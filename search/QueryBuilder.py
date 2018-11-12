from enum import Enum

class QueryType(Enum):
    QNone = 0
    QAll = 1
    QOr = 2
    QAnd = 3

class Query:
    def __init__(self, op, tri=set(), sub=[]):
        self.op = op
        self.tri = tri
        self.sub = sub
    
un_op = {'?', '+', '*'}
bin_op = {'|', '.'}
par = {'(', ')'}

def get_string_set(tree):
	if tree == None:
		return set()

	if tree['val'] not in (un_op | bin_op | par):
		return {tree['val']}

	s1 = get_string_set(tree['op1'])
	s2 = get_string_set(tree['op2'])

	if tree['val'] == '|':
		return s1 | s2

	if tree['val'] == '?':	
		s1.add('')
		return s1

	if tree['val'] == '+' or tree['val'] == '*':
		s3 = set()
		s3 |= s1
		for i in s1:
			if len(i) <= 1:
				s3.add(i + i)
		if tree['val'] == '*':
			s3.add('')
		return s3

	if tree['val'] == '.':
		s3 = set()
		for i in s1:
			for j in s2:
				s3.add(i + j)
		return s3

def get_query(tree):
    string_set = get_string_set(tree)
    sub = []
    for s in string_set:
        n = len(s)
        if n < 3:
            return Query(QueryType.QAll)
        tri = set()
        for i in range(n - 2):
            tri.add(s[i:i+3])
        sub += [Query(QueryType.QAnd, tri=tri)]
    return Query(QueryType.QOr, sub=sub)