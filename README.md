# pycodesearch
Code Search in large codebase
## Indexing
* python cindex.py folder_to_index
## Search
* python csearch.py regex
* uses re for now

## Hierarchical Explanation

Broad classification of code search tools based on how the user enters the search query
* Search with strings
* Search with code
* Search with natural language
* Search with regex
  * Regex over entire codebase: This approach is slow because regular expression over entire text takes `O(n)` time (Thompson NFA).
  * Regex over an index: This approach aims to reduce the number of files over which the regex is performed by building an index. E.g. **Google Code Search**
  
    Google Code Search has the following components
    1. Build an index
    2. Prepare trigrams from user query
    3. Lookup in the index, regex search over the corresponding files
  