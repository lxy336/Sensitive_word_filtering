class TreeNode:
    def __init__(self):
        self.children = {}
        self.is_end = False
 
 
class Tree:
    def __init__(self):
        self.root = TreeNode()
 
    def insert(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                node.children[char] = TreeNode()
            node = node.children[char]
        node.is_end = True
 
    def search(self, word):
        node = self.root
        for char in word:
            if char not in node.children:
                return False
            node = node.children[char]
        return node.is_end
 
 
def trie_tree_filter_words(text, words):
    tree = Tree()
    for word in words:
        tree.insert(word)
 
    result = []
    for i in range(len(text)):
        node = tree.root
        for j in range(i, len(text)):
            if text[j] not in node.children:
                break
            node = node.children[text[j]]
            if node.is_end:
                result.append((i, j))
    for start_index, end_index in result[::-1]:
        text = text[:start_index] + '*' * (end_index - start_index + 1) + text[end_index + 1:]
    return text
 
 