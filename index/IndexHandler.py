import pickle
import os
import logging
from collections import defaultdict
from datetime import datetime

logging.basicConfig(level="INFO")


class IndexHandler:

    def __init__(self):
        self.index_file = "index.pkl"
        self.index = defaultdict(set)
        self.files = []
        self.fileid = 0

    # builds the index for the contents of a directory
    def build(self, root):
        logging.info("index creation starting")
        start_time = datetime.now()
        for root, _, files in os.walk(root):
            for file in files:
                file = os.path.join(root, file)
                self.add_file(file)
        logging.info("index created %s", str(datetime.now() - start_time))
        with open(self.index_file, "wb") as fp:
            pickle.dump((self.index, self.files), fp)
        logging.info("index written to disk %s", str(datetime.now() - start_time))

    # adds contents of given file to the trigram index
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
        with open(self.index_file, "rb") as fp:
            index = pickle.load(fp)
        return index


if __name__ == "__main__":
    index_handler = IndexHandler()
    index_handler.build("cpython-master")
    # logging.info(index_handler.read())
