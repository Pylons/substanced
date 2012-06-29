from ..interfaces import (
    ICatalogable,
    )

from ..event import (
    subscribe_added,
    subscribe_will_be_removed,
    subscribe_modified,
    )
    
from ..service import (
    find_services,
    find_service,
    )

from ..util import (
    postorder,
    oid_of,
    )

@subscribe_added()
def object_added(event):
    """ An IObjectAdded event subscriber which indexes an object and and its
    children in every catalog service in the lineage of the object. Depends
    upon the fact that ``substanced.objectmap.object_will_be_added`` to
    assign an ``__objectid__`` to the object and its children will have been
    fired before this gets fired.
    """
    obj = event.object
    catalogs = find_services(obj, 'catalog')
    if not catalogs:
        return
    for node in postorder(obj):
        if ICatalogable.providedBy(node):
            objectid = oid_of(node)
            for catalog in catalogs:
                catalog.index_doc(objectid, node)

@subscribe_will_be_removed()
def object_will_be_removed(event):
    """ Unindex an object and its children from every catalog service object's
    lineage; an :class:`substanced.event.ObjectWillBeRemoved` event
    subscriber"""
    obj = event.object
    objectmap = find_service(obj, 'objectmap')
    catalogs = find_services(obj, 'catalog')
    if objectmap is None or not catalogs:
        return
    objectids = objectmap.pathlookup(obj)
    for catalog in catalogs:
        for oid in catalog.family.IF.intersection(objectids, catalog.objectids):
            catalog.unindex_doc(oid)

@subscribe_modified()
def object_modified(event):
    """ Reindex a single object (non-recursive) in every catalog service in
    the object's lineage; an :class:`substanced.event.ObjectModifed` event
    subscriber"""
    obj = event.object
    catalogs = find_services(obj, 'catalog')
    for catalog in catalogs:
        objectid = oid_of(obj)
        catalog.reindex_doc(objectid, obj)

