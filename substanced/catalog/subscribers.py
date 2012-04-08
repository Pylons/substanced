import BTrees
from zope.interface import Interface

from pyramid.events import subscriber

from ..interfaces import (
    ICatalogable,
    IObjectAddedEvent,
    IObjectWillBeRemovedEvent,
    IObjectModifiedEvent,
    )
    
from ..objectmap import find_objectmap
from ..util import postorder

from . import find_catalog

@subscriber([Interface, IObjectAddedEvent])
def object_added(obj, event):
    """ Depends upon substance.objectmap.object_will_be_added to be fired
    before this gets fired to assign an __objectid__ to all nodes"""
    catalog = find_catalog(obj)
    if catalog is None:
        return
    for node in postorder(obj):
        if ICatalogable.providedBy(node):
            objectid = node.__objectid__
            objectid = catalog.index_doc(objectid, node)

@subscriber([Interface, IObjectWillBeRemovedEvent])
def object_will_be_removed(obj, event):
    objectmap = find_objectmap(obj)
    catalog = find_catalog(obj)
    if objectmap is None or catalog is None:
        return
    objectids = objectmap.pathlookup(obj)
    for oid in BTrees.family32.IF.intersection(objectids, catalog.objectids):
        catalog.unindex_doc(oid)

@subscriber([Interface, IObjectModifiedEvent])
def object_modified(obj, event):
    """ Reindex a single piece of content (non-recursive); an
    ObjectModifedEvent event subscriber """
    objectid = obj.__objectid__
    catalog = find_catalog(obj)
    if catalog is not None:
        if ICatalogable.providedBy(obj):
            catalog.reindex_doc(objectid, obj)

