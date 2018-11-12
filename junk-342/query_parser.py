"""
Parse the user query to generate candidate trigrams
Ref: https://swtch.com/~rsc/regexp/regexp4.html
"""

# import re
from nltk import trigrams
from pickle import load, dump
from time import time
from random import randrange

r = r"a(bc)+d"
ROOT_DIR = None
INDEX_FILE = "somefile.pkl"


class CodeSearch:

    def __init__(self):
        self.trigram_index = None
        self.load_index()

    def parse_query(self, raw_query=""):
        """
        This function converts a given regex to candidate trigrams
        """
        pass

    def parse_argv(self, argv_str):
        # -b indicates to rebuild the index before searching
        pass

    def load_index(self, index_file=INDEX_FILE):
        with open(index_file, "rb") as f:
            self.trigram_index = load(f)

    def dump_index(self, index_file=INDEX_FILE):
        with open(index_file, "wb") as f:
            dump(self.trigram_index, f)

    def build_index(self):
        pass


if __name__ == "__main__":
    docs = [chr(randrange(256)) for x in range(int(4e6))]
    index = dict()
    start = time()
    for fileid, tri in enumerate(trigrams(docs)):
        tri = ''.join(tri)
        if tri not in index:
            index[tri] = []
        index[tri].append(fileid)
    print("index created", time()-start, "s")

    with open(INDEX_FILE, "wb") as fp:
        dump(index, fp)  # pickle.dump, not json

    print("index written to disk", time()-start, "s")
