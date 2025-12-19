def replace_filter_words(text, words):
    # 按长度排序，避免短词覆盖长词
    sorted_words = sorted(words, key=len, reverse=True)

    result = []
    i = 0
    while i < len(text):
        found = False
        # 检查是否匹配任何敏感词
        for word in sorted_words:
            if text[i:i+len(word)] == word:
                start_index = i
                end_index = i + len(word) - 1  
                result.append((start_index, end_index))
                i += len(word)  # 跳过已匹配的部分
                found = True
                break
        if not found:
            i += 1

    # 倒序替换，避免位置偏移
    for start_index, end_index in result[::-1]:
        text = text[:start_index] + '*' * (end_index - start_index + 1) + text[end_index + 1:]
    return text

