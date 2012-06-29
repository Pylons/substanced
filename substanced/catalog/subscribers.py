from zope.interface import Interface

from pyramid.events import subscriber

from ..interfaces import (
    ICatalogable,
    IObjectAdded,
    IObjectWillBeRemoved,
    IObjectModified,
    )
    
from ..service import (
    find_services,
    find_service,
    )

from ..util import (
    postorder,
    oid_of,
    )

@subscriber([Interface, IObjectAdded])
def object_added(obj, event):
    """ An IObjectAdded event subscriber which indexes an object and and its
    children in every catalog service in the lineage of the object. Depends
    upon the fact that ``substanced.objectmap.object_will_be_added`` to
    assign an ``__objectid__`` to the object and its children will have been
    fired before this gets fired.
    """
    catalogs = find_services(obj, 'catalog')
    if not catalogs:
        return
    for node in postorder(obj):
        if ICatalogable.providedBy(node):
            objectid = oid_of(node)
            for catalog in catalogs:
                catalog.index_doc(objectid, node)

@subscriber([Interface, IObjectWillBeRemoved])
def object_will_be_removed(obj, event):
    """ Unindex an object and its children from every catalog service object's
    lineage; an :class:`substanced.event.ObjectWillBeRemoved` event
    subscriber"""
    objectmap = find_service(obj, 'objectmap')
    catalogs = find_services(obj, 'catalog')
    if objectmap is None or not catalogs:
        return
    objectids = objectmap.pathlookup(obj)
    for catalog in catalogs:
        for oid in catalog.family.IF.intersection(objectids, catalog.objectids):
            catalog.unindex_doc(oid)

@subscriber([ICatalogable, IObjectModified])
def object_modified(obj, event):
    """ Reindex a single object (non-recursive) in every catalog service in
    the object's lineage; an :class:`substanced.event.ObjectModifed` event
    subscriber"""
    catalogs = find_services(obj, 'catalog')
    for catalog in catalogs:
        objectid = oid_of(obj)
        catalog.reindex_doc(objectid, obj)

