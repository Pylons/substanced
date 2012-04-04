from zope.interface import Interface

from pyramid.events import subscriber

from ..interfaces import (
    IFolder,
    ICatalogable,
    IObjectAddedEvent,
    IObjectWillBeRemovedEvent,
    IObjectModifiedEvent,
    )
    
from ..catalog import find_catalog
from ..objectmap import find_objectmap

def _postorder(startnode):
    def visit(node):
        if IFolder.providedBy(node):
            for child in node.values():
                for result in visit(child):
                    yield result
        yield node
    return visit(startnode)

@subscriber([Interface, IObjectAddedEvent])
def object_added(obj, event):
    """ Index content (an IObjectAddedEvent subscriber) """
    catalog = find_catalog(obj)
    objectmap = find_objectmap(obj)
    if objectmap is not None:
        for node in _postorder(obj):
            objectid = getattr(node, '__objectid__', None)
            if objectid is None:
                objectid = node.__objectid__ = objectmap.add(obj)
            else:
                objectmap.add(obj, objectid)
            if ICatalogable.providedBy(node) and catalog is not None:
                catalog.index_doc(objectid, node)

@subscriber([Interface, IObjectWillBeRemovedEvent])
def object_removed(obj, event):
    """ IObjectWillBeRemovedEvent subscriber.
    """
    # NB: do not conditionalize this with an ICatalogable.providedBy(obj);
    # the object being removed may not itself be catalogable, but it may
    # contain catalogable objects (e.g. it might be a folder with catalogable
    # items within it).
    catalog = find_catalog(obj)
    objectmap = find_objectmap(obj)
    if objectmap is not None:
        objectids = objectmap.remove(obj)
        if catalog is not None:
            for objectid in objectids:
                if objectid in catalog.objectids:
                    catalog.unindex_doc(objectid)

@subscriber([Interface, IObjectModifiedEvent])
def object_modified(obj, event):
    """ Reindex a single piece of content (non-recursive); an
    ObjectModifed event subscriber """
    objectmap = find_objectmap(obj)
    if objectmap is not None:
        objectid = objectmap.objectid_for(obj)
        if objectid is None:
            object_added(obj, event)
            objectid = obj.__objectid__
        else:
            catalog = find_catalog(obj)
            if ICatalogable.providedBy(obj) and catalog is not None:
                catalog.reindex_doc(objectid, obj)

def includeme(config): # pragma: no cover
    config.scan('substanced.subscribers')
    
