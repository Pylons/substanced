from ..content import find_services

from ..event import (
    subscribe_added,
    subscribe_removed,
    subscribe_modified,
    )

from ..util import (
    postorder,
    oid_of,
    )

from . import (
    catalog_view_factory_for, 
    CatalogViewWrapper,
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
        catalog_view_factory = catalog_view_factory_for(node, event.registry)
        if catalog_view_factory:
            objectid = oid_of(node)
            for catalog in catalogs:
                catalog.index_doc(
                    objectid,
                    CatalogViewWrapper(node, catalog_view_factory)
                    )

@subscribe_removed()
def object_removed(event):
    """ Unindex an object and its children from every catalog service object's
    lineage; an :class:`substanced.event.ObjectRemoved` event
    subscriber"""
    parent = event.parent
    catalogs = find_services(parent, 'catalog')
    for catalog in catalogs:
        for oid in catalog.family.IF.intersection(
            event.removed_oids, catalog.objectids
            ):
            catalog.unindex_doc(oid)

@subscribe_modified()
def object_modified(event):
    """ Reindex a single object (non-recursive) in every catalog service in
    the object's lineage; an :class:`substanced.event.ObjectModifed` event
    subscriber"""
    obj = event.object
    catalog_view_factory = catalog_view_factory_for(obj, event.registry)
    if catalog_view_factory:
        wrapper = CatalogViewWrapper(obj, catalog_view_factory)
        catalogs = find_services(obj, 'catalog')
        for catalog in catalogs:
            objectid = oid_of(obj)
            catalog.reindex_doc(objectid, wrapper)

