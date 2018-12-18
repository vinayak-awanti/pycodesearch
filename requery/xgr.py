from xeger import Xeger
from collections import Counter
from query import Query


def get_trigrams(raw_str):
    prev = raw_str[:3]
    yield prev
    for j in range(3, len(raw_str)):
        prev = prev[1:] + raw_str[j]
        yield prev


def xegerQuery(query):
    c = Counter()
    total = 0
    
    for i in range(1, 4**len(query)):
        x = Xeger(limit=i)
        res = x.xeger(query)
        total += 1
        trigrams = list(set(get_trigrams(res)))
        c.update(trigrams)
    
    tri = []
    for trigram in c:
        if c[trigram] == total:
            tri.append(trigram)
    
    if len(tri) == 0:
        q = Query(Query.QAll)       
    else:
        q = Query(Query.QAnd, trigram=tri)
    
    return q


if __name__ == '__main__':
    print(xegerQuery(r"abc+de"))
