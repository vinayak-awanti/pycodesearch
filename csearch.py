import os
import re
import sys
import mmap
import logging
import argparse
from time import time
from tabulate import tabulate
import pickle
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
parser.add_argument("-d", "--directory", help="name of the directory", default='empty')
parser.add_argument("-s", "--show", help="show the candidate documents", action="store_true")
parser.add_argument("-t", "--test", help="Test", action="store_true")
logging.basicConfig(level="INFO")
args = parser.parse_args()
reg = args.regex

try:
    compiled_regex = re.compile(reg)
except:
    logging.info("Invalid regular expression")
    quit()

regex_tree = parse(reg)
flag = 1
# index = Index()
logging.info("constructing trigram query")


def full_regex_search(file_names):
    logging.info("full regular expression search starting")
    st = time()
    ctr = 0
    for filename in file_names:
        try:
            with open(filename, 'r+') as f:
                mo = compiled_regex.search(f.read())
                if mo:
                    ctr += 1
                    if args.show:
                        logging.info(" Found in -  %s", filename)
        except:
            pass
    logging.info("full regular expression search took %s", str(time() - st))
    return ctr, time() - st


if args.index:
    if args.directory == 'empty':
        logging.info('Please read usage --help')
        quit()
    else:
        if os.path.exists(args.directory):
            index = Index(args.directory)
        else:
            logging.info('No such file exists')
            quit()

if args.test:
    try:
        os.system("rm my.pkl")
    except:
        pass

    regexs = ["a(b+|c+)d", "(abc|cba)def", "abc+de", "ab(cd)*ef", "def|lambda", "a*(bcd|efg)",
              "(a|b|c)+@(a|b|c)+(\.(a|b|c))+"]

    for i in range(len(regexs)):
        os.system("python3 csearch.py -a demo " + '"' + regexs[i] + '"')
        print(i + 1, "done")
    with open("my.pkl", 'rb') as f:
        x = pickle.load(f)

    for i in range(1, 4):
        for j in range(5):
            x[j][i] /= len(regexs)

    print(tabulate(x, headers=['Algorithm', 'Space', 'Query Time', 'Search Time', 'Found in'], tablefmt='orgtbl'))
    quit()


def demo():
    logging.info("Comparison of various codesearch algorithms\n")
    lis = []
    algo = ['Brute Force', 'Google Code Search', 'RESET', 'XEGER', 'FREE']
    func = [deepcopy, allQuery, regexpQuery, regex_tree, regexp_query, regex_tree, xegerQuery, args.regex, freeQuery,
            regex_tree]
    for i in range(5):
        try:
            lis.append([algo[i]])
            st = time()
            query = func[2 * i](func[2 * i + 1])
            logging.info(" query generated for %s %s", algo[i], query)
            dur_q = time() - st
            index = Index()
            tot = index.get_filecount()
            logging.info("%s identified %d candidate files", algo[i], tot)
            candid = index.get_candidate_fileids(query)
            file_names = index.get_filenames(candid)
            ctr, dur_s = full_regex_search(file_names, args.regex)
            # print(i, len(candid), ctr)
            lis[-1].extend([str(round((len(candid) * 100) / tot, 2)) + ' %', str(round(dur_q, 5)) + ' seconds',
                            str(round(dur_s, 5)) + ' seconds', ctr])
        except Exception as e:
            pass
    print('\n')
    test(lis)
    print(tabulate(lis, headers=['Algorithm', 'Space', 'Query Time', 'Search Time', 'Found in'], tablefmt='orgtbl'))


def test(lis):
    try:
        with open('my.pkl', 'rb') as f:
            nlis = pickle.load(f)
    except:
        nlis = [['Brute Force', 0, 0, 0], ['Google Code Search', 0, 0, 0], ['RESET', 0, 0, 0], ['XEGER', 0, 0, 0],
                ['FREE', 0, 0, 0]]

    for i in range(1, 4):
        for j in range(5):
            y = lis[j][i].split(' ')
            nlis[j][i] += float(y[0])

    with open('my.pkl', 'wb') as f:
        pickle.dump(nlis, f)


if args.algo == 'empty':
    print('Please read usage --help')
    quit()
else:
    algo_dict = {'bruteforce': [deepcopy, allQuery],
                 'gcs': [regexpQuery, regex_tree],
                 'reset': [regexp_query, regex_tree],
                 'xeger': [xegerQuery, args.regex],
                 'free': [freeQuery, regex_tree]}
    st = time()
    if args.algo in algo_dict:
        query = algo_dict[args.algo][0](algo_dict[args.algo][1])
    elif args.algo == 'demo':
        demo()
        flag = 0
    else:
        logging.info('Invalid algorithm')
        flag = 0
    dur = time() - st
    if flag:
        logging.info("%s took %s to construct trigram query", args.algo, str(dur))
        logging.info("trigram query: %s", str(query))

        index = Index()
        candid = index.get_candidate_fileids(query)

        logging.info("%s identified %d candidate files", args.algo, len(candid))

        file_names = index.get_filenames(candid)

        ctr, x = full_regex_search(file_names, args.regex)
        logging.info("%d files have substring matching %s", ctr, reg)
