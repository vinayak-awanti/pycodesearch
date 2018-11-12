from index.IndexHandler import IndexHandler
from search.QueryBuilder import QueryType, Query
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

    # returns candidate fileids
    def query(self, tri_query):
        if tri_query.op == QueryType.QAll:
            return set(range(len(self.files)))

        func = self.list_and if tri_query.op == QueryType.QAnd else self.list_or
        if len(tri_query.tri) == 0:
            lst = self.query(tri_query.sub[0])
            for i in range(1, len(tri_query.sub)):
                lst = func(lst, self.query(tri_query.sub[i]))
        else:
            for tri in tri_query.tri:
                lst = self.index[tri]
                break
            for tri in tri_query.tri:
                lst = func(lst, self.index[tri])
        return lst

    def get_filenames(self, fileids):
        return list(map(lambda x: self.files[x], fileids))

if __name__ == '__main__':
    start = time()
    query_handler = QueryHandler()
    logging.info(query_handler.list_or([0, 2], 'oog'))
    logging.info(query_handler.list_and([0, 2], 'Goo'))
    logging.info(time()-start)
    quit()
    while True:
        logging.info(query_handler.query([input()]))
