import BTrees
from zope.interface import Interface

from pyramid.events import subscriber

from ..interfaces import (
    ICatalogable,
    IObjectAdded,
    IObjectWillBeRemoved,
    IObjectModified,
    )
    
from ..service import find_service
from ..util import (
    postorder,
    oid_of,
    )

@subscriber([Interface, IObjectAdded])
def object_added(obj, event):
    """ Index an object and and its children in the closest catalog; an
    IObjectAdded event subscriber.  Depends upon
    substance.objectmap.object_will_be_added to have been fired
    before this gets fired to assign an __objectid__ to the object.
    """
    catalog = find_service(obj, 'catalog')
    if catalog is None:
        return
    for node in postorder(obj):
        if ICatalogable.providedBy(node):
            objectid = oid_of(node)
            objectid = catalog.index_doc(objectid, node)

@subscriber([Interface, IObjectWillBeRemoved])
def object_will_be_removed(obj, event):
    """ Unindex an object and its children in the closest catalog; an
    :class:`substanced.event.ObjectWillBeRemoved` event subscriber"""
    objectmap = find_service(obj, 'objectmap')
    catalog = find_service(obj, 'catalog')
    if objectmap is None or catalog is None:
        return
    objectids = objectmap.pathlookup(obj)
    for oid in BTrees.family32.IF.intersection(objectids, catalog.objectids):
        catalog.unindex_doc(oid)

@subscriber([ICatalogable, IObjectModified])
def object_modified(obj, event):
    """ Reindex a single object (non-recursive) in the closest catalog; an
    :class:`substanced.event.ObjectModifed` event subscriber """
    catalog = find_service(obj, 'catalog')
    if catalog is not None:
        objectid = oid_of(obj)
        catalog.reindex_doc(objectid, obj)

