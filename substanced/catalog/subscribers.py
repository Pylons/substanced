from zope.interface.interfaces import ComponentLookupError

import logging

from pyramid.traversal import resource_path
from pyramid.settings import asbool
from pyramid.events import (
    ApplicationCreated,
    subscriber,
    )
from pyramid.request import Request

from ..event import (
    subscribe_added,
    subscribe_removed,
    subscribe_modified,
    subscribe_acl_modified,
    )

from ..objectmap import find_objectmap

from ..util import (
    postorder,
    get_oid,
    find_catalogs,
    get_dotted_name,
    )

from . import Catalog

logger = logging.getLogger(__name__)

@subscribe_added()
def object_added(event):
    """ An IObjectAdded event subscriber which indexes an object and and its
    children in every catalog service in the lineage of the object. Depends
    upon the fact that ``substanced.objectmap.object_will_be_added`` to
    assign an ``__oid__`` to the object and its children will have been
    fired before this gets fired.
    """
    obj = event.object
    catalogs = find_catalogs(obj)
    if not catalogs:
        return
    for node in postorder(obj):
        oid = get_oid(node, None)
        if oid is not None:
            for catalog in catalogs:
                catalog.index_doc(oid, node)

@subscribe_removed()
def object_removed(event):
    """ Unindex an object and its children from every catalog service object's
    lineage; an :class:`substanced.event.ObjectRemoved` event
    subscriber"""
    parent = event.parent
    catalogs = find_catalogs(parent)
    removed = event.removed_oids
    for catalog in catalogs:
        for oid in catalog.family.IF.intersection(removed, catalog.objectids):
            catalog.unindex_doc(oid)

@subscribe_modified()
def object_modified(event):
    """ Reindex a single object (non-recursive) in every catalog service in
    the object's lineage; an :class:`substanced.event.ObjectModifed` event
    subscriber"""
    obj = event.object
    oid = get_oid(obj, None)
    if oid is not None:
        catalogs = find_catalogs(obj)
        for catalog in catalogs:
            catalog.reindex_doc(oid, obj)

@subscribe_acl_modified()
def acl_modified(event):
    resource = event.object
    registry = event.registry
    catalogs = find_catalogs(resource)

    for catalog in catalogs:
        # hellishly expensive
        indexes = catalog.values()
        for index in indexes:
            index_path = resource_path(index)
            if registry.content.istype(index, 'Allowed Index'):
                for node in postorder(resource):
                    logger.info('%s: reindexing %s' % (index_path, node))
                    oid = get_oid(node, None)
                    if oid is not None:
                        index.reindex_doc(oid, node)

@subscriber(ApplicationCreated)
def on_startup(event):
    app = event.object
    registry = app.registry
    settings = getattr(registry, 'settings', {})
    autosync = asbool(settings.get('substanced.autosync_catalogs', False))
    if autosync:
        request = Request.blank('/autosync_catalogs') # path is meaningless
        request.registry = registry
        root = app.root_factory(request)
        objectmap = find_objectmap(root)
        if objectmap is not None:
            oids = objectmap.get_extent(get_dotted_name(Catalog))
            for oid in oids:
                catalog = objectmap.object_for(oid)
                if catalog is not None:
                    try:
                        catalog.update_indexes(registry=registry, reindex=True)
                    except ComponentLookupError:
                        # could not find a catalog factory
                        pass
                    
