import logging
import os
import pickle
from query import Query
from time import time
from collections import defaultdict

logging.basicConfig(level="INFO")

class Index:
    def __init__(self, root = None):
        self.index_file = "index.pkl"
        if os.path.exists(self.index_file) and root == None:
            with open(self.index_file, "rb") as fp:
                self.index, self.files = pickle.load(fp)
            self.fileid = len(self.files)    
        else:
            self.index = defaultdict(set)
            self.files = []
            self.fileid = 0
            if root == None:
                logging.info('Error give file name')
                quit()
            else:    
                self.build(root)          

    def build(self, root):
        logging.info("index creation starting")
        start_time = time()
        for root, _, files in os.walk(root):
            for file in files:
                file = os.path.join(root, file)
                self.add_file(file)
        logging.info("index created %s", str(time() - start_time))
        with open(self.index_file, "wb") as fp:
            pickle.dump((self.index, self.files), fp)
        logging.info("index written to disk %s", str(time() - start_time))

    def add_file(self, file):
        try:
            with open(file, "r") as fp:
                doc = fp.read()
            prev = doc[:3]
            if len(prev) == 3:
                self.index[prev].add(self.fileid)
            for char in doc[3:]:
                prev = prev[1:] + char
                self.index[prev].add(self.fileid)
            self.fileid += 1
            self.files.append(file)
        except UnicodeDecodeError:
            # logging.info("Couldn't read", file)
            pass

    # returns the index
    def read(self):
        return self.index

    # returns intersection of posting lists
    def list_and(self, lst1, lst2):
        return lst1 & lst2
    
    # returns union of posting lists
    def list_or(self, lst1, lst2):
        return lst1 | lst2

    # returns candidate file ids
    def get_candidate_fileids(self, q):
        if q.op == Query.QNone:
            return set()

        if q.op == Query.QAll:
            return set(range(len(self.files)))

        if q.op == Query.QAnd:
            candid = None
            for t in q.trigram:
                candid = self.index[t]
                break

            for t in q.trigram:
                candid = self.list_and(candid, self.index[t])

            if candid is None:
                for s in q.sub:
                    candid = self.get_candidate_fileids(s)

            for s in q.sub:
                candid = self.list_and(candid, self.get_candidate_fileids(s))

        if q.op == Query.QOr:
            candid = set()
            for t in q.trigram:
                candid = self.list_or(candid, self.index[t])
            for s in q.sub:
                candid = self.list_or(candid, self.get_candidate_fileids(s))

        return set() if candid is None else candid

    def get_filenames(self, fileids):
        return list(map(lambda x: self.files[x], fileids))

    def get_filecount(self):
        return len(self.files)

if __name__ == "__main__":
    index = Index()
    index.build("gcs")
    logging.info(index.read())
