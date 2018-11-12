def get_trigrams(raw_str):
    prev = raw_str[:3]
    yield prev
    for i in range(3, len(raw_str)):
        prev = prev[1:] + raw_str[i]
        yield prev
