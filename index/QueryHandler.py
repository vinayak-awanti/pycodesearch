from IndexHandler import IndexHandler

class QueryHandler:
  def __init__(self):
    index_handler = IndexHandler()
    self.index, self.files = index_handler.read()

  # returns intersection of posting lists of the given trigrams
  def list_and(self, lst1, tri):
    i, j = 0, 0
    lst2, lst3 = self.index[tri], []
    n, m = len(lst1), len(lst2)
    while i < n and j < m:
      if lst1[i] < lst2[j]:
        i += 1
      elif lst1[i] > lst2[j]:
        j += 1
      else:
        lst3.append(lst1[i])
        i += 1
        j += 1
    return lst3

  # returns union of posting lists of the given trigrams
  def list_or(self, lst1, tri):
    i, j = 0, 0
    n, lst2, lst3 = len(lst1), self.index[tri], []
    m = len(lst2)
    while(i < n and j < m):
      x, y = lst1[i], lst2[j]
      if(x == y):
        lst3.append(x)
        i += 1
        j += 1
      elif(x < y):
        lst3.append(x)
        i += 1
      else:
        lst3.append(y)
        j += 1
    if(i < n):
      lst3.extend(lst1[i:])
    if(j < m):
      lst3.append(lst2[j:])
    
    return lst3      


query_handler = QueryHandler()

print(query_handler.list_or([0, 2], 'oog'))
print(query_handler.list_and([0, 2], 'Goo'))