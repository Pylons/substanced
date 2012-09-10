from ..content import find_services

from ..event import (
    subscribe_added,
    subscribe_will_be_removed,
    subscribe_modified,
    )

from ..objectmap import find_objectmap

from ..util import (
    postorder,
    oid_of,
    )

from . import is_catalogable

@subscribe_added()
def object_added(event):
    """ An IObjectAdded event subscriber which indexes an object and and its
    children in every catalog service in the lineage of the object. Depends
    upon the fact that ``substanced.objectmap.object_will_be_added`` to
    assign an ``__objectid__`` to the object and its children will have been
    fired before this gets fired.
    """
    obj = event.object
    catalogs = find_objectmap(obj)
    if not catalogs:
        return
    for node in postorder(obj):
        if is_catalogable(node, event.registry):
            objectid = oid_of(node)
            for catalog in catalogs:
                catalog.index_doc(objectid, node)

@subscribe_will_be_removed()
def object_will_be_removed(event):
    """ Unindex an object and its children from every catalog service object's
    lineage; an :class:`substanced.event.ObjectWillBeRemoved` event
    subscriber"""
    obj = event.object
    objectmap = find_objectmap(obj)
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

