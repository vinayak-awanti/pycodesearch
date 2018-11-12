class NFA:
    epsilon = 'Є'
    def __init__(self, regex):
        self.q0 = None
        self.qf = None
        self.regex = regex
        self.build_nfa()

    class Node:
        def __init__(self, state, is_start=False, is_end=False):
            self.state = state
            self.edges = []  # list of tuples, character, Node
            self.is_start = is_start
            self.is_end = is_end

    def build_nfa(self):
        state = 0
        self.start_state = self.Node(state)
        state += 1

