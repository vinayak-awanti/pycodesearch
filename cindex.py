import os
import sys
from index import IndexHandler

if len(sys.argv) != 2:
    print("usage: python cindex.py path")
    quit()

index_handler = IndexHandler.IndexHandler()
index_handler.build(os.path.abspath(sys.argv[1]))
