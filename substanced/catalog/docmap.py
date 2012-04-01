import random
import sys

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

class DocumentMap(object):
    
    nextid = None

    def __init__(self):
        self.docid_to_path = {}
        self.path_to_docid = {}
        self.pathindex = {}

    def new_docid(self, path_tuple):
        while True:
            if self.nextid is None:
                self.nextid = random.randrange(-sys.maxint, sys.maxint)

            docid = self.nextid
            self.nextid += 1

            if docid not in self.docid_to_path:
                return docid

            self.nextid = None
            
    def add(self, path_tuple, docid=_marker):
        if path_tuple in self.path_to_docid:
            raise ValueError('path %s already exists' % (path_tuple,))
        
        if not isinstance(path_tuple, tuple):
            raise ValueError('add accepts only a tuple, got' % (path_tuple,))
        
        if docid is _marker:
            docid = self.new_docid(path_tuple)
        elif docid in self.docid_to_path:
            raise ValueError('docid %s already exists' % docid)

        self.path_to_docid[path_tuple] = docid
        self.docid_to_path[docid] = path_tuple

        pathlen = len(path_tuple)

        for x in range(pathlen):
            els = path_tuple[:x+1]
            dmap = self.pathindex.setdefault(els, {})
            level = pathlen - len(els)
            didset = dmap.setdefault(level, set())
            didset.add(docid)

        return docid

    def remove(self, docid_or_path_tuple):
        if isinstance(docid_or_path_tuple, int):
            path_tuple = self.docid_to_path[docid_or_path_tuple]
        elif isinstance(docid_or_path_tuple, tuple):
            path_tuple = docid_or_path_tuple
        else:
            raise ValueError(
                'remove accepts only a docid or a path tuple, got' % (
                    docid_or_path_tuple,)
                )

        pathlen = len(path_tuple)

        dmap = self.pathindex.get(path_tuple)

        # rationale: if this key isn't present, no path added ever contained it
        if dmap is None:
            return set()

        removed = set()
        # sorted() only for clarity during tests
        items = sorted(dmap.items())

        # this can be done with a min= option to BTree.items method
        for k, dm in self.pathindex.items():
            if k[:pathlen] == path_tuple:
                for didset in dm.values():
                    removed.update(didset)
                    for did in didset:
                        if did in self.docid_to_path:
                            p = self.docid_to_path[did]
                            del self.docid_to_path[did]
                            del self.path_to_docid[p]
                # XXX mutation while iterating
                del self.pathindex[k]

        for x in range(pathlen-1):
            offset = x + 1
            els = path_tuple[:pathlen-offset]
            dmap2 = self.pathindex.get(els)
            for level, didset in items:

                i = level + offset
                didset2 = dmap2.get(i)

                if didset2 is None:
                    continue

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
            for d, didset in sorted(dmap.items()):
                
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

if __name__ == '__main__':

    def split(s):
        return (u'',) + tuple(filter(None, s.split(u'/')))

    def l(path, depth=None):
        path_tuple = split(path)
        return sorted(list(docmap.pathlookup(path_tuple, depth)))

    docmap = DocumentMap()
    docmap.nextid = 1

    root = split('/')
    a = split('/a')
    ab = split('/a/b')
    abc = split('/a/b/c')
    z = split('/z')

    did1 = docmap.add(ab)
    did2 = docmap.add(abc)
    did3 = docmap.add(a)
    did4 = docmap.add(root)
    did5 = docmap.add(z)

    # /
    nodepth = l('/')
    assert nodepth == [did1, did2, did3, did4, did5], nodepth
    depth0 = l('/', depth=0)
    assert depth0 == [did4], depth0
    depth1 = l('/', depth=1)
    assert depth1 == [did3, did4, did5], depth1
    depth2 = l('/', depth=2)
    assert depth2 == [did1, did3, did4, did5], depth2
    depth3 = l('/', depth=3)
    assert depth3 == [did1, did2, did3, did4, did5], depth3
    depth4 = l('/', depth=4)
    assert depth4 == [did1, did2, did3, did4, did5], depth4
    
    # /a
    nodepth = l('/a')
    assert nodepth == [did1, did2, did3], nodepth
    depth0 = l('/a', depth=0)
    assert depth0 == [did3], depth0
    depth1 = l('/a', depth=1)
    assert depth1 == [did1, did3], depth1
    depth2 = l('/a', depth=2)
    assert depth2 == [did1, did2, did3], depth2
    depth3 = l('/a', depth=3)
    assert depth3 == [did1, did2, did3], depth3
    
    # /a/b
    nodepth = l('/a/b')
    assert nodepth == [did1, did2], nodepth
    depth0 = l('/a/b', depth=0)
    assert depth0 == [did1], depth0
    depth1 = l('/a/b', depth=1)
    assert depth1 == [did1, did2], depth1
    depth2 = l('/a/b', depth=2)
    assert depth2 == [did1, did2], depth2
    
    # /a/b/c
    nodepth = l('/a/b/c')
    assert nodepth == [did2], nodepth
    depth0 = l('/a/b/c', depth=0)
    assert depth0 == [did2], depth0
    depth1 = l('/a/b/c', depth=1)
    assert depth1 == [did2], depth1

    # remove '/a/b'
    removed = docmap.remove(did1)
    assert removed == set([1,2])

    # /a/b/c
    nodepth = l('/a/b/c')
    assert nodepth == [], nodepth
    depth0 = l('/a/b/c', depth=0)
    assert depth0 == [], depth0
    depth1 = l('/a/b/c', depth=1)
    assert depth1 == [], depth1

    # /a/b
    nodepth = l('/a/b')
    assert nodepth == [], nodepth
    depth0 = l('/a/b', depth=0)
    assert depth0 == [], depth0
    depth1 = l('/a/b', depth=1)
    assert depth1 == [], depth1

    # /a
    nodepth = l('/a')
    assert nodepth == [did3], nodepth
    depth0 = l('/a', depth=0)
    assert depth0 == [did3], depth0
    depth1 = l('/a', depth=1)
    assert depth1 == [did3], depth1

    # /
    nodepth = l('/')
    assert nodepth == [did3, did4, did5], nodepth
    depth0 = l('/', depth=0)
    assert depth0 == [did4], depth0
    depth1 = l('/', depth=1)
    assert depth1 == [did3, did4, did5], depth1

    assert docmap.pathindex == {(u'',): {0: set([4]), 1: set([3, 5])}, 
                                (u'', u'a'): {0: set([3])},
                                (u'', u'z'): {0: set([5])}}
    assert docmap.docid_to_path == {3: (u'', u'a'), 4: (u'',), 5: (u'', u'z')}
    assert docmap.path_to_docid == {(u'', u'z'): 5, (u'', u'a'): 3, (u'',): 4}

    # remove '/'
    removed = docmap.remove((u'',))
    assert removed == set([3,4,5])

    assert docmap.pathindex == {}
    print docmap.docid_to_path
    
    assert docmap.docid_to_path == {}
    assert docmap.path_to_docid == {}
    
    print 'OK'
