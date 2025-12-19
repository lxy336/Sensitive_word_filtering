import ahocorasick
 
 
def aho_corasick_filter_words(text, words):
    # 处理空敏感词列表的情况
    if not words:
        return text

    A = ahocorasick.Automaton()
    for index, word in enumerate(words):
        A.add_word(word, (index, word))
    A.make_automaton()

    result = []
    for end_index, (_, original_value) in A.iter(text):
        start_index = end_index - len(original_value) + 1
        result.append((start_index, end_index))

    for start_index, end_index in result[::-1]:
        text = text[:start_index] + '*' * (end_index - start_index + 1) + text[end_index + 1:]
    return text
 
 
