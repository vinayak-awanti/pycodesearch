import mmap
import re
import sys
import logging

logging.basicConfig(level="INFO")

from time import time
from index import QueryHandler
from regexp import regexpQuery
from reparser.regex_parser import parse
from search.QueryBuilder import regexp_query, Query, QAll

if len(sys.argv) < 2:
    print("usage: python csearch.py regex algorithm showfiles")
    quit()


showfiles = True if len(sys.argv) == 4 and sys.argv[3] == "true" else False
if len(sys.argv) >= 3:
    alg = sys.argv[2]
reg = sys.argv[1]

try:
    re.compile(reg)
except:
    print("invalid regular expression")
    quit()

def full_regex_search(file_names, showfiles=False):
    logging.info("full regular expression search starting")
    st = time()
    ctr = 0
    for filename in file_names:
        with open(filename, 'r+') as f:
            try:
                data = mmap.mmap(f.fileno(), 0)
                mo = re.search(sys.argv[1].encode('ASCII'), data)
                if mo:
                    if showfiles:
                        print("found in", filename, mo.span())
                    ctr += 1
            except:
                pass
    logging.info("full regular expression search took %s", str(time() - st))
    return ctr

regex_tree = parse(reg)

logging.info("constructing trigram query")
if alg == "reset":
    st = time()
    query = regexp_query(regex_tree)
    dur = time() - st
elif alg == "gcs":
    st = time()
    query = regexpQuery(regex_tree)
    dur = time() - st
elif alg == "force":
    st = time()
    query = Query(QAll)
    dur = time() - st
else:
    print("invalid algorithm")
    quit()
logging.info("%s took %s to construct trigram query", alg, str(dur))
logging.info("trigram query: %s", str(query))

query_handler = QueryHandler.QueryHandler()
candid = query_handler.query(query)

logging.info("%s identified %d candidate files", alg, len(candid))

file_names = query_handler.get_filenames(candid)

ctr = full_regex_search(file_names, showfiles)
logging.info("%d files have substring matching %s", ctr, reg)