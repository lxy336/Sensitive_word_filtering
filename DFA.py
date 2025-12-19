class DFA:
    def __init__(self, words):
        self.words = words
        self.build()
 
    def build(self):
        self.transitions = {}
        self.fails = {}
        self.outputs = {}
        state = 0
        for word in self.words:
            current_state = 0
            for char in word:
                next_state = self.transitions.get((current_state, char), None)
                if next_state is None:
                    state += 1
                    self.transitions[(current_state, char)] = state
                    current_state = state
                else:
                    current_state = next_state
            self.outputs[current_state] = word
        queue = []
        for (start_state, char), next_state in self.transitions.items():
            if start_state == 0:
                queue.append(next_state)
                self.fails[next_state] = 0
        while queue:
            r_state = queue.pop(0)
            for (state, char), next_state in self.transitions.items():
                if state == r_state:
                    queue.append(next_state)
                    fail_state = self.fails[state]
                    while (fail_state, char) not in self.transitions and fail_state != 0:
                        fail_state = self.fails[fail_state]
                    self.fails[next_state] = self.transitions.get((fail_state, char), 0)
                    if self.fails[next_state] in self.outputs:
                        self.outputs[next_state] += ', ' + self.outputs[self.fails[next_state]]
 
    def search(self, text):
        state = 0
        result = []
        for i, char in enumerate(text):
            while (state, char) not in self.transitions and state != 0:
                state = self.fails[state]
            state = self.transitions.get((state, char), 0)
            if state in self.outputs:
                # 处理多个匹配的情况
                words_found = self.outputs[state].split(', ')
                for word in words_found:
                    start_pos = i - len(word) + 1
                    result.append((start_pos, i))
        return result
 
 
def DFA_filter_words(text, words):
    dfa = DFA(words)
    result = []
    for start_index, end_index in dfa.search(text):
        result.append((start_index, end_index))
    for start_index, end_index in result[::-1]:
        text = text[:start_index] + '*' * (end_index - start_index + 1) + text[end_index + 1:]
    return text
