import os
import re
import sys
import mmap
import logging
import argparse
from time import time
from tabulate import tabulate
logging.basicConfig(level="INFO")

from copy import deepcopy
from query import allQuery
from requery.gcs import regexpQuery
from requery.reset import regexp_query
from requery.xgr import xegerQuery
from requery.free import freeQuery
from index import Index
from reparser.regex_parser import parse

parser = argparse.ArgumentParser()
parser.add_argument("-a", "--algo", help="type of algorithm to be used", default="empty")
parser.add_argument("regex", help="regex to search", default="empty")
parser.add_argument("-i", "--index", help="build a new index file", action="store_true")
parser.add_argument("-d", "--directory", help="name of the directory", default = 'empty')
parser.add_argument("-s", "--show", help="show the candidate documents",action="store_true")

args = parser.parse_args()
reg = args.regex

try:
    re.compile(reg)
except:
    logging.info("Invalid regular expression")
    quit()

regex_tree = parse(reg)
flag = 1
index = Index()
logging.info("constructing trigram query")

def full_regex_search(file_names, regex):
    logging.info("full regular expression search starting")
    st = time()
    ctr = 0
    for filename in file_names:
        with open(filename, 'r+') as f:
            try:
                data = mmap.mmap(f.fileno(), 0)
                mo = re.search(regex.encode('ASCII'), data)
                if mo:
                    ctr += 1
            except:
                pass
    logging.info("full regular expression search took %s", str(time() - st))
    return (ctr, time() - st)

if(args.index):     
    if(args.directory == 'empty'):
        logging.info('Please read usage --help')
        quit()
    else:
        if(os.path.exists(args.directory)):
            index = Index(args.directory)
        else:
            logging.info('No such file exists')
            quit()

def demo():
    logging.info("Comparison of various codesearch algorithms\n")
    lis = [] 
    algo = ['Brute Force', 'Google Code Search', 'RESET', 'XEGER']
    func = [deepcopy, allQuery,regexpQuery, regex_tree, regexp_query, regex_tree, xegerQuery, args.regex]
    for i in range(4):
        try:
            lis.append([algo[i]])
            st = time()
            query = func[2*i](func[2*i + 1])
            logging.info(" query generated for %s %s", algo[i], query)
            dur_q = time() - st
            index = Index()
            tot = index.get_filecount()
            candid = index.get_candidate_fileids(query)
            file_names = index.get_filenames(candid)
            ctr, dur_s = full_regex_search(file_names, args.regex)
            # print(i, len(candid), ctr)
            lis[-1].extend([str(round((len(candid)*100)/tot, 2)) + ' %', str(round(dur_q, 5))+ ' seconds', str(round(dur_s ,5)) + ' seconds', ctr])
        except:
            pass   
    print('\n')        
    print(tabulate(lis, headers=['Algorithm', 'Space', 'Query Time', 'Search Time', 'Found in'], tablefmt='orgtbl'))
        


if(args.algo == 'empty'):
    print('Please read usage --help')
    quit()
else:
    if(args.algo == 'bruteforce'):
        st = time()
        query = deepcopy(allQuery)
        dur = time() - st
    elif(args.algo == 'gcs'):
        st = time()
        query = regexpQuery(regex_tree)
        dur = time() - st
    elif(args.algo == 'reset'):
        st = time()
        query = regexp_query(regex_tree)
        dur = time() - st
    elif(args.algo == 'xeger'):
        st = time()
        query = xegerQuery(args.regex)
    elif(args.algo == 'free'):
        # TODO
        x = 1
    elif(args.algo == 'demo'):
        demo()
        flag = 0    
    else:
        logging.info('Invalid algorithm')   
        flag = 0
    if(flag):
        logging.info("%s took %s to construct trigram query", args.algo, str(dur))
        logging.info("trigram query: %s", str(query))

        index = Index()
        candid = index.get_candidate_fileids(query)

        logging.info("%s identified %d candidate files", args.algo, len(candid))

        file_names = index.get_filenames(candid)

        if(args.show):
            for file in file_names:
                logging.info(file)
        
        ctr, x = full_regex_search(file_names, args.regex)
        logging.info("%d files have substring matching %s", ctr, reg)   
