import BTrees
from zope.interface import Interface

from pyramid.events import subscriber

from ..interfaces import (
    ICatalogable,
    IObjectAddedEvent,
    IObjectWillBeRemovedEvent,
    IObjectModifiedEvent,
    )
    
from ..service import find_service
from ..util import (
    postorder,
    oid_of,
    )

@subscriber([Interface, IObjectAddedEvent])
def object_added(obj, event):
    """ Depends upon substance.objectmap.object_will_be_added to be fired
    before this gets fired to assign an __objectid__ to all nodes"""
    catalog = find_service(obj, 'catalog')
    if catalog is None:
        return
    for node in postorder(obj):
        if ICatalogable.providedBy(node):
            objectid = oid_of(node)
            objectid = catalog.index_doc(objectid, node)

@subscriber([Interface, IObjectWillBeRemovedEvent])
def object_will_be_removed(obj, event):
    objectmap = find_service(obj, 'objectmap')
    catalog = find_service(obj, 'catalog')
    if objectmap is None or catalog is None:
        return
    objectids = objectmap.pathlookup(obj)
    for oid in BTrees.family32.IF.intersection(objectids, catalog.objectids):
        catalog.unindex_doc(oid)

@subscriber([Interface, IObjectModifiedEvent])
def object_modified(obj, event):
    """ Reindex a single piece of content (non-recursive); an
    ObjectModifedEvent event subscriber """
    objectid = oid_of(obj)
    catalog = find_service(obj, 'catalog')
    if catalog is not None:
        if ICatalogable.providedBy(obj):
            catalog.reindex_doc(objectid, obj)

