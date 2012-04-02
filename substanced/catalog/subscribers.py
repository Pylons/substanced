from zope.interface import Interface

from pyramid.events import subscriber
from pyramid.traversal import resource_path_tuple

from ..interfaces import (
    IFolder,
    ICatalogable,
    IObjectAddedEvent,
    IObjectWillBeRemovedEvent,
    IObjectModifiedEvent,
    )
    
from . import find_catalog

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
    if catalog is not None:
        for node in _postorder(obj):
            if ICatalogable.providedBy(node):
                path_tuple = resource_path_tuple(node)
                docid = getattr(node, 'docid', None)
                if docid is None:
                    docid = node.docid = catalog.document_map.add(path_tuple)
                else:
                    catalog.document_map.add(path_tuple, docid)
                catalog.index_doc(docid, node)

@subscriber([Interface, IObjectWillBeRemovedEvent])
def object_removed(obj, event):
    """ IObjectWillBeRemovedEvent subscriber.
    """
    # NB: do not conditionalize this with an ICatalogable.providedBy(obj);
    # the object being removed may not itself be catalogable, but it may
    # contain catalogable objects (e.g. it might be a folder with catalogable
    # items within it).
    catalog = find_catalog(obj)
    if catalog is not None:
        path_tuple = resource_path_tuple(obj)
        docids = catalog.document_map.remove(path_tuple)
        for docid in docids:
            catalog.unindex_doc(docid)

@subscriber([Interface, IObjectModifiedEvent])
def object_modified(obj, event):
    """ Reindex a single piece of content (non-recursive); an
    ObjectModifed event subscriber """
    if ICatalogable.providedBy(obj):
        catalog = find_catalog(obj)
        if catalog is not None:
            path_tuple = resource_path_tuple(obj)
            docid = catalog.document_map.path_to_docid.get(path_tuple)
            if docid is None:
                object_added(obj, event)
            else:
                catalog.reindex_doc(docid, obj)

