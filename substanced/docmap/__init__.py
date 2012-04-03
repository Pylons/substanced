import random

from persistent import Persistent

import BTrees

from BTrees.OOBTree import OOBTree
from BTrees.IOBTree import IOBTree
from BTrees.OIBTree import OIBTree
from BTrees.IIBTree import IISet

from ..interfaces import IDocmapSite

from pyramid.traversal import find_interface

def find_docmap(context):
    site = find_interface(context, IDocmapSite)
    if site is None:
        return
    return site.docmap

"""
Pathindex data structure of document map:

{pathtuple:{level:set_of_docids, ...}, ...}

>>> map = DocumentMap()

For example if a document map with an otherwise empty pathindex has
``add('/a/b/c')`` called on it, and the docid for ``/a/b/c`` winds up being
``1``, the path index will end up looking like this:

>>> map.add('/a/b/c')
>>> map.pathindex

{(u'',):                  {3: set([1])}, 
 (u'', u'a'):             {2: set([1])}, 
 (u'', u'a', u'b'):       {1: set([1])},
 (u'', u'a', u'b', u'c'): {0: set([1])}}

(Level 0 is "this path")

If we then ``add('/a')`` and the result winds up as docid 2, the pathindex
will look like this:

>>> map.add('/a')
>>> map.pathindex

{(u'',):                  {1: set([2]), 3: set([1])}, 
 (u'', u'a'):             {0: set([2]), 2: set([1])}, 
 (u'', u'a', u'b'):       {1: set([1])},
 (u'', u'a', u'b', u'c'): {0: set([1])}}

If we then add '/z' (and its docid is 3):

>>> map.add('/z')
>>> map.pathindex

{(u'',):                  {1: set([2, 3]), 3: set([1])}, 
 (u'', u'a'):             {0: set([2]), 2: set([1])}, 
 (u'', u'a', u'b'):       {1: set([1])},
 (u'', u'a', u'b', u'c'): {0: set([1])},
 (u'', u'z'):             {0: set([3])}}

And so on and so forth as more items are added.  It is an error to attempt to
add an item to document map with a path that already exists in the document
map.

If '/a' (docid 2) is then removed, the pathindex is adjusted to remove
references to the docid represented by '/a' *and* any children (in this case,
there's a child at '/a/b/c').

>>> map.remove(2)
>>> map.pathindex

{(u'',):      {1: set([3])},
 (u'', u'z'): {0: set([3])}}
 
"""

_marker = object()

class DocumentMap(Persistent):
    
    _v_nextid = None
    _randrange = random.randrange

    def __init__(self):
        self.docid_to_path = IOBTree()
        self.path_to_docid = OIBTree()
        self.pathindex = OOBTree()

    def new_docid(self):
        while True:
            if self._v_nextid is None:
                self._v_nextid = self._randrange(BTrees.IOBTree.family.minint, 
                                                 BTrees.IOBTree.family.maxint)

            docid = self._v_nextid
            self._v_nextid += 1

            if docid not in self.docid_to_path:
                return docid

            self._v_nextid = None
            
    def add(self, path_tuple, docid=_marker):
        if path_tuple in self.path_to_docid:
            raise ValueError('path %s already exists' % (path_tuple,))
        
        if not isinstance(path_tuple, tuple):
            raise ValueError('add accepts only a tuple, got %s' % (path_tuple,))
        
        if docid is _marker:
            docid = self.new_docid()
        elif docid in self.docid_to_path:
            raise ValueError('docid %s already exists' % docid)

        self.path_to_docid[path_tuple] = docid
        self.docid_to_path[docid] = path_tuple

        pathlen = len(path_tuple)

        for x in range(pathlen):
            els = path_tuple[:x+1]
            dmap = self.pathindex.setdefault(els, IOBTree())
            level = pathlen - len(els)
            didset = dmap.setdefault(level, IISet())
            didset.add(docid)

        return docid

    def remove(self, docid_or_path_tuple):
        if isinstance(docid_or_path_tuple, int):
            path_tuple = self.docid_to_path[docid_or_path_tuple]
        elif isinstance(docid_or_path_tuple, tuple):
            path_tuple = docid_or_path_tuple
        else:
            raise ValueError(
                'remove accepts only a docid or a path tuple, got %s' % (
                    (docid_or_path_tuple,))
                )

        pathlen = len(path_tuple)

        dmap = self.pathindex.get(path_tuple)

        # rationale: if this key isn't present, no path added ever contained it
        if dmap is None:
            return IISet()

        removed = set()
        # sorted() only for clarity during tests
        items = dmap.items()

        removepaths = []
        # this can be done with a min= option to BTree.items method
        for k, dm in self.pathindex.items(min=path_tuple):
            if k[:pathlen] == path_tuple:
                for didset in dm.values():
                    removed.update(didset)
                    for did in didset:
                        if did in self.docid_to_path:
                            p = self.docid_to_path[did]
                            del self.docid_to_path[did]
                            del self.path_to_docid[p]
                # dont mutate while iterating
                removepaths.append(k)
            else:
                break

        for k in removepaths:
            del self.pathindex[k]

        for x in range(pathlen-1):

            offset = x + 1
            els = path_tuple[:pathlen-offset]
            dmap2 = self.pathindex[els]
            for level, didset in items:

                i = level + offset
                didset2 = dmap2[i]

                for did in didset:
                    if did in didset2:
                        didset2.remove(did)
                        # adding to removed and removing from docid_to_path
                        # and path_to_docid should have been taken care of
                        # above in the for k, dm in self.pathindex.items()
                        # loop
                        assert did in removed, did
                        assert not did in self.docid_to_path, did

                if not didset2:
                    del dmap2[i]
                    
        return removed

    def pathlookup(self, path_tuple, depth=None, include_origin=True):
        if not isinstance(path_tuple, tuple):
            raise ValueError(
                'pathlookup accepts only a tuple, got %s' % (path_tuple,))
        
        dmap = self.pathindex.get(path_tuple)

        if dmap is None:
            raise StopIteration
        
        if depth is None:
            for d, didset in dmap.items():
                
                if d == 0 and not include_origin:
                    continue

                for v in didset:
                    yield v

        else:
            for d in range(depth+1):

                if d == 0 and not include_origin:
                    continue

                didset = dmap.get(d)

                if didset is None:
                    continue
                else:
                    for v in didset:
                        yield v


