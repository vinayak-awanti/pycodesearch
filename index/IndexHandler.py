import pickle
import os
import logging
from collections import defaultdict
from datetime import datetime

logging.basicConfig(level="INFO")

class IndexHandler:
  def __init__(self):
    self.index_file = "index.pkl"
  
  # builds the index for the contents of a directory
  def build(self, dir):
    self.index = defaultdict(list)
    self.files = []
    self.fileid = 0
    logging.info("index creation starting")
    start_time = datetime.now()
    for root, _, files in os.walk(dir):
      for file in files:
        self.add_file(os.path.join(root, file))
      self.files.extend(files)
    logging.info("index created %s", str(datetime.now() - start_time))
    with open(self.index_file, "wb") as fp:
      pickle.dump((self.index, self.files), fp)
    logging.info("index written to disk %s", str(datetime.now() - start_time))
  
  # adds contents of given file to the trigram index
  def add_file(self, file):
    with open(file, "r") as fp:
      doc = fp.read()
    for i in range(len(doc) - 2):
      tri = doc[i:i+3]
      if len(self.index[tri]) == 0 or self.index[tri][-1] < self.fileid:
        self.index[tri].append(self.fileid)
    self.fileid += 1

  # returns the index
  def read(self):
    with open(self.index_file, "rb") as fp:
      index = pickle.load(fp)
    return index

if __name__ == "__main__":
  index_handler = IndexHandler()
  index_handler.build("gcs")
  print(index_handler.read())