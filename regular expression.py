import re


def regular_expression_filter_words(text, words):
    # 创建正则表达式模式，按长度排序避免短词覆盖长词
    sorted_words = sorted(words, key=len, reverse=True)
    pattern = '|'.join(re.escape(word) for word in sorted_words)

    result = []
    for match in re.finditer(pattern, text):
        start_index = match.start()
        end_index = match.end() - 1  
        result.append((start_index, end_index))

    for start_index, end_index in result[::-1]:
        text = text[:start_index] + '*' * (end_index - start_index + 1) + text[end_index + 1:]
    return text

 