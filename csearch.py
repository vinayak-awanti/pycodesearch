import mmap
import os
import sys
import re
from index import QueryHandler
from search.RegexHandler import parse
from search.QueryBuilder import get_query

if len(sys.argv) != 2:
    print("usage: python csearch.py regex")
    quit()

regex = parse(sys.argv[1])
if regex == None:
    print("invalid regex")
    quit()

tri_query = get_query(regex)
query_handler = QueryHandler.QueryHandler()
candid = query_handler.query(tri_query)
filenames = query_handler.get_filenames(candid)

for filename in filenames:
    with open(filename, 'r+') as f:
        data = mmap.mmap(f.fileno(), 0)
        mo = re.search(sys.argv[1].encode('ASCII'), data)
        if mo:
            print("found in", filename, mo.span())
