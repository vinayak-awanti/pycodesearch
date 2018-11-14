from index.IndexHandler import IndexHandler
from search.QueryBuilder import QAll, QAnd, QNone, QOr
import logging
from time import time

logging.basicConfig(level="INFO")

class QueryHandler:
    def __init__(self):
        index_handler = IndexHandler()
        self.index, self.files = index_handler.read()

    # returns intersection of posting lists
    def list_and(self, lst1, lst2):
        return lst1 & lst2
    
    # returns union of posting lists
    def list_or(self, lst1, lst2):
        return lst1 | lst2

    # returns candidate file ids
    def query(self, q):
        if q.op == QNone:
            return set()
        if q.op == QAll:
            return set(range(len(self.files)))

        candid = None
        for t in q.trigram:
            candid = self.index[t]
            break

        f = self.list_and if q.op == QAnd else self.list_or
        for t in q.trigram:
            f(candid, self.index[t])

        if candid is None:
            for s in q.sub:
                candid = self.query(s)

        for s in q.sub:
            f(candid, self.query(s))

        # logging.info("candid: %s", str(candid))
        return set() if candid is None else candid

    def get_filenames(self, fileids):
        return list(map(lambda x: self.files[x], fileids))

if __name__ == '__main__':
    start = time()
    query_handler = QueryHandler()
    logging.info(time()-start)
    quit()
    while True:
        logging.info(query_handler.query([input()]))
