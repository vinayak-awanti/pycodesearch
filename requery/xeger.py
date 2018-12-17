from xeger import Xeger
from collections import Counter
from time import time

def get_trigrams(raw_str):
    prev = raw_str[:3]
    yield prev
    for j in range(3, len(raw_str)):
        prev = prev[1:] + raw_str[j]
        yield prev


# fix this 
query = r"abc+de"
def xegerQuery(query):
    c = Counter()
    total = 0

    start = time()
    for i in range(1, 4**len(query)):
        x = Xeger(limit=i)
        res = x.xeger(query)
        total += 1
        # print(res)
        trigrams = list(set(get_trigrams(res)))
        c.update(trigrams)
    lis = []   
    # print(total, c)
    for trigram in c:
        if c[trigram] == total:
            lis.append(trigram)
    
    # do something        
    
    return ['XEGER', ]


if __name__ == '__main__':
    xgerQuery(r"abc+de")