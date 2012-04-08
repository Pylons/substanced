import random
from zope.interface import Interface

from persistent import Persistent

import BTrees

from pyramid.traversal import resource_path_tuple
from pyramid.events import subscriber

from ..service import find_service
from ..util import postorder

from ..interfaces import (
    IObjectWillBeAddedEvent,
    IObjectRemovedEvent,
    )

def find_objectmap(context):
    return find_service(context, 'objectmap')

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

    family = BTrees.family32

    def __init__(self):
        self.objectid_to_path = self.family.IO.BTree()
        self.path_to_objectid = self.family.OI.BTree()
        self.pathindex = self.family.OO.BTree()

    def new_objectid(self):
        while True:
            if self._v_nextid is None:
                self._v_nextid = self._randrange(self.family.minint, 
                                                 self.family.maxint)

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
            
    def add(self, obj, path_tuple):
        if not isinstance(path_tuple, tuple):
            raise ValueError('path_tuple argument must be a tuple')

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
            omap = self.pathindex.setdefault(els, self.family.IO.BTree())
            level = pathlen - len(els)
            oidset = omap.setdefault(level, self.family.IF.Set())
            oidset.add(objectid)

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

        omap = self.pathindex.get(path_tuple)

        # rationale: if this key isn't present, no path added ever contained it
        if omap is None:
            return set()

        removed = set()
        # sorted() only for clarity during tests
        items = omap.items()

        removepaths = []
        # this can be done with a min= option to BTree.items method
        for k, dm in self.pathindex.items(min=path_tuple):
            if k[:pathlen] == path_tuple:
                for oidset in dm.values():
                    removed.update(oidset)
                    for oid in oidset:
                        if oid in self.objectid_to_path:
                            p = self.objectid_to_path[oid]
                            del self.objectid_to_path[oid]
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
            omap2 = self.pathindex[els]
            for level, oidset in items:

                i = level + offset
                oidset2 = omap2[i]

                for oid in oidset:
                    if oid in oidset2:
                        oidset2.remove(oid)
                        # adding to removed and removing from objectid_to_path
                        # and path_to_objectid should have been taken care of
                        # above in the for k, dm in self.pathindex.items()
                        # loop
                        assert oid in removed, oid
                        assert not oid in self.objectid_to_path, oid

                if not oidset2:
                    del omap2[i]
                    
        return removed

    def _get_path_tuple(self, obj_or_path_tuple):
        if hasattr(obj_or_path_tuple, '__parent__'):
            path_tuple = resource_path_tuple(obj_or_path_tuple)
        elif isinstance(obj_or_path_tuple, tuple):
            path_tuple = obj_or_path_tuple
        else:
            raise ValueError(
                'pathlookup must be provided a traversable object or a '
                'path tuple, got %s' % (obj_or_path_tuple,))
        return path_tuple
    
    def navgen(self, obj_or_path_tuple, depth=1):
        path_tuple = self._get_path_tuple(obj_or_path_tuple)
        return self._navgen(path_tuple, depth)

    def _navgen(self, path_tuple, depth):
        omap = self.pathindex.get(path_tuple)
        if omap is None:
            return []
        oidset = omap.get(1)
        result = []
        if oidset is None:
            return result
        newdepth = depth-1
        if newdepth > -1:
            for oid in oidset:
                pt = self.objectid_to_path[oid]
                result.append(
                    {'path':pt,
                     'children':self._navgen(pt, newdepth),
                     'name':pt[-1],
                     }
                    )
        return result

    def pathlookup(self, obj_or_path_tuple, depth=None, include_origin=True):
        path_tuple = self._get_path_tuple(obj_or_path_tuple)
        omap = self.pathindex.get(path_tuple)

        result = self.family.IF.Set()

        if omap is None:
            return result
        
        if depth is None:
            for d, oidset in omap.items():
                
                if d == 0 and not include_origin:
                    continue

                result.update(oidset)

        else:
            for d in range(depth+1):

                if d == 0 and not include_origin:
                    continue

                oidset = omap.get(d)

                if oidset is None:
                    continue
                else:
                    result.update(oidset)

        return result

@subscriber([Interface, IObjectWillBeAddedEvent])
def object_will_be_added(obj, event):
    """ Give content an __objectid__ and index it (an IObjectWillBeAddedEvent
     subscriber, so objects always have an __objectid__ within the more
     convenient IObjectAddedEvent)"""
    parent = event.parent
    objectmap = find_objectmap(parent)
    if objectmap is None:
        return
    if getattr(obj, '__parent__', None):
        raise ValueError(
            'obj %s added to folder %s already has a __parent__ attribute, '
            'please remove it completely from its existing parent (%s) before '
            'trying to readd it to this one' % (obj, parent, obj.__parent__)
            )
    basepath = resource_path_tuple(event.parent)
    name = event.name
    for node in postorder(obj):
        node_path = resource_path_tuple(node)
        path_tuple = basepath + (name,) + node_path[1:]
        objectmap.add(node, path_tuple) # gives node an __objectid__

@subscriber([Interface, IObjectRemovedEvent])
def object_removed(obj, event):
    """ IObjectRemovedEvent subscriber.
    """
    parent = event.parent
    objectmap = find_objectmap(parent)
    if objectmap is None:
        return
    objectid = obj.__objectid__
    objectmap.remove(objectid)

def includeme(config): # pragma: no cover
    config.scan('substanced.objectmap')
    
