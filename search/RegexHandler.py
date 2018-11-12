import logging

logging.basicConfig(level="INFO")

class Stack:
	def __init__(self):
		self.arr = []
	def push(self, elem):
		self.arr.append(elem)
	def pop(self):
		return self.arr.pop()
	def empty(self):
		return len(self.arr) == 0
	def top(self):
		return self.arr[-1]
	def disp(self):
		print(*self.arr)

un_op = {'?', '+', '*'}
bin_op = {'|', '.'}
par = {'(', ')'}

# adds . to denote explicit concatenation
def format_regex(regex):
    formatted_regex = ""
    for i in range(len(regex) - 1):
        formatted_regex += regex[i]
        if regex[i] != '(' and regex[i+1] != ')' and regex[i+1] not in (un_op|bin_op) and regex[i] not in bin_op:
            formatted_regex += '.'
    formatted_regex += regex[-1]
    return formatted_regex

precedence = {'(': 0, '|': 1, '.': 2, '*': 3, '+': 3, '?': 3}

# converts given infix expression to its tree form
def parse(infifx_expr):
	infifx_expr = format_regex(infifx_expr)
	logging.info("infix_expr - %s", infifx_expr)
	outq, s = Stack(), Stack()

	def new_node():
		val = s.pop()
		op2 = outq.pop()
		op1 = None
		if val['val'] in bin_op:
			op1 = outq.pop()
		if op1 == None:
			op1, op2 = op2, op1
		outq.push({'val': val['val'], 'op1': op1, 'op2': op2})

	for ch in infifx_expr:
		if ch not in (un_op | bin_op | par):
			outq.push({'val': ch})
		elif ch == '(':
			s.push({'val': ch})
		elif ch == ')':
			while not s.empty() and s.top()['val'] != '(':
				new_node()
			s.pop()
		else:
			while not s.empty() and precedence.get(ch, 4) <= precedence.get(s.top()['val'], 4):
				new_node()
			s.push({'val': ch})
    
	while not s.empty():
		new_node()
	return outq.top()

if __name__ == "__main__":
    parse("a(b|c+)d*")