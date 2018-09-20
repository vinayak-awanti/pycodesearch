# A Set is a sparse set of integer values.
# http://research.swtch.com/2008/03/using-uninitialized-memory-for-fun-and.html
import logging

logging.basicConfig(level="INFO")


class Set(object):
    """Implementation of Sparse Set"""

    def __init__(self, max_len):
        self.sparse = [None] * max_len
        self.dense = [None] * max_len
        self.cur_len = 0
        self.max_len = max_len

    def Reset(self):
        self.cur_len = 0

    def Add(self, x):
        if x < self.max_len:
            self.dense[self.cur_len] = x
            self.sparse[x] = self.cur_len
            self.cur_len += 1
        else:
            logging.error("Error inserted element out of range")

    def Has(self, x):
        if x < self.max_len:
            return self.sparse[x] < self.max_len and self.dense[self.sparse[x]] == x
        else:
            logging.error("Error searched element out of range")

    def Len(self):
        return self.cur_len

    def Dense(self):
        return self.dense


def NewSet(max):
    return Set(max_len=max)


if __name__ == "__main__":
    myset = Set(10)
    myset.Add(5)
    myset.Add(1)
    myset.Add(4)
    logging.info(myset.Dense())
    logging.info(myset.Len())
    logging.info(myset.sparse)
