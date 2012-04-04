import random

from persistent import Persistent

import BTrees

from BTrees.OOBTree import OOBTree
from BTrees.IOBTree import IOBTree
from BTrees.OIBTree import OIBTree
from BTrees.IIBTree import IISet

from ..interfaces import IObjectmapSite

from pyramid.traversal import (
    find_interface,
    resource_path_tuple,
    )

def find_objectmap(context):
    site = find_interface(context, IObjectmapSite)
    if site is None:
        return
    return site.objectmap

"""
Pathindex data structure of object map:

{pathtuple:{level:set_of_objectids, ...}, ...}

>>> map = ObjectMap()

For example if a object map with an otherwise empty pathindex has
``add('/a/b/c')`` called on it, and the objectid for ``/a/b/c`` winds up being
``1``, the path index will end up looking like this:

>>> map.add('/a/b/c')
>>> map.pathindex

{(u'',):                  {3: set([1])}, 
 (u'', u'a'):             {2: set([1])}, 
 (u'', u'a', u'b'):       {1: set([1])},
 (u'', u'a', u'b', u'c'): {0: set([1])}}

(Level 0 is "this path")

If we then ``add('/a')`` and the result winds up as objectid 2, the pathindex
will look like this:

>>> map.add('/a')
>>> map.pathindex

{(u'',):                  {1: set([2]), 3: set([1])}, 
 (u'', u'a'):             {0: set([2]), 2: set([1])}, 
 (u'', u'a', u'b'):       {1: set([1])},
 (u'', u'a', u'b', u'c'): {0: set([1])}}

If we then add '/z' (and its objectid is 3):

>>> map.add('/z')
>>> map.pathindex

{(u'',):                  {1: set([2, 3]), 3: set([1])}, 
 (u'', u'a'):             {0: set([2]), 2: set([1])}, 
 (u'', u'a', u'b'):       {1: set([1])},
 (u'', u'a', u'b', u'c'): {0: set([1])},
 (u'', u'z'):             {0: set([3])}}

And so on and so forth as more items are added.  It is an error to attempt to
add an item to object map with a path that already exists in the object
map.

If '/a' (objectid 2) is then removed, the pathindex is adjusted to remove
references to the objectid represented by '/a' *and* any children (in this case,
there's a child at '/a/b/c').

>>> map.remove(2)
>>> map.pathindex

{(u'',):      {1: set([3])},
 (u'', u'z'): {0: set([3])}}
 
"""

_marker = object()

class ObjectMap(Persistent):
    
    _v_nextid = None
    _randrange = random.randrange

    def __init__(self, site):
        self.site = site
        self.objectid_to_path = IOBTree()
        self.path_to_objectid = OIBTree()
        self.pathindex = OOBTree()

    def new_objectid(self):
        while True:
            if self._v_nextid is None:
                self._v_nextid = self._randrange(BTrees.IOBTree.family.minint, 
                                                 BTrees.IOBTree.family.maxint)

            objectid = self._v_nextid
            self._v_nextid += 1

            if objectid not in self.objectid_to_path:
                return objectid

            self._v_nextid = None

    def objectid_for(self, obj_or_path_tuple):
        if isinstance(obj_or_path_tuple, tuple):
            path_tuple = obj_or_path_tuple
        elif hasattr(obj_or_path_tuple, '__parent__'):
            path_tuple = resource_path_tuple(obj_or_path_tuple)
        else:
            raise ValueError(
                'objectid_for accepts a traversable object or a path tuple, '
                'got %s' % (obj_or_path_tuple,))
        return self.path_to_objectid.get(path_tuple)

    def path_for(self, objectid):
        return self.objectid_to_path.get(objectid)
            
    def add(self, obj):
        if not hasattr(obj, '__parent__'):
            raise ValueError(
                'add accepts a traversable object got %s' % (obj,))
        path_tuple = resource_path_tuple(obj)
        objectid = getattr(obj, '__objectid__', _marker)
        
        if objectid is _marker:
            objectid = self.new_objectid()
            obj.__objectid__ = objectid
        elif objectid in self.objectid_to_path:
            raise ValueError('objectid %s already exists' % (objectid,))

        if path_tuple in self.path_to_objectid:
            raise ValueError('path %s already exists' % (path_tuple,))

        self.path_to_objectid[path_tuple] = objectid
        self.objectid_to_path[objectid] = path_tuple

        pathlen = len(path_tuple)

        for x in range(pathlen):
            els = path_tuple[:x+1]
            dmap = self.pathindex.setdefault(els, IOBTree())
            level = pathlen - len(els)
            didset = dmap.setdefault(level, IISet())
            didset.add(objectid)

        return objectid

    def remove(self, obj_objectid_or_path_tuple):
        if hasattr(obj_objectid_or_path_tuple, '__parent__'):
            path_tuple = resource_path_tuple(obj_objectid_or_path_tuple)
        elif isinstance(obj_objectid_or_path_tuple, int):
            path_tuple = self.objectid_to_path[obj_objectid_or_path_tuple]
        elif isinstance(obj_objectid_or_path_tuple, tuple):
            path_tuple = obj_objectid_or_path_tuple
        else:
            raise ValueError(
                'Value passed to remove must be a traversable '
                'object, an object id, or a path tuple, got %s' % (
                    (obj_objectid_or_path_tuple,)))

        pathlen = len(path_tuple)

        dmap = self.pathindex.get(path_tuple)

        # rationale: if this key isn't present, no path added ever contained it
        if dmap is None:
            return set()

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
                        if did in self.objectid_to_path:
                            p = self.objectid_to_path[did]
                            del self.objectid_to_path[did]
                            del self.path_to_objectid[p]
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
                        # adding to removed and removing from objectid_to_path
                        # and path_to_objectid should have been taken care of
                        # above in the for k, dm in self.pathindex.items()
                        # loop
                        assert did in removed, did
                        assert not did in self.objectid_to_path, did

                if not didset2:
                    del dmap2[i]
                    
        return removed

    def pathlookup(self, obj_or_path_tuple, depth=None, include_origin=True):
        if hasattr(obj_or_path_tuple, '__parent__'):
            path_tuple = resource_path_tuple(obj_or_path_tuple)
        elif isinstance(obj_or_path_tuple, tuple):
            path_tuple = obj_or_path_tuple
        else:
            raise ValueError(
                'pathlookup must be provided a traversable object or a '
                'path tuple, got %s' % (obj_or_path_tuple,))
        
        dmap = self.pathindex.get(path_tuple)

        result = IISet()

        if dmap is None:
            return result
        
        if depth is None:
            for d, didset in dmap.items():
                
                if d == 0 and not include_origin:
                    continue

                result.update(didset)

        else:
            for d in range(depth+1):

                if d == 0 and not include_origin:
                    continue

                didset = dmap.get(d)

                if didset is None:
                    continue
                else:
                    result.update(didset)

        return result


