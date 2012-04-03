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
    
from ..catalog import find_catalog
from ..docmap import find_docmap

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
    docmap = find_docmap(obj)
    if docmap is not None:
        for node in _postorder(obj):
            path_tuple = resource_path_tuple(node)
            docid = getattr(node, '__docid__', None)
            if docid is None:
                docid = node.__docid__ = docmap.add(path_tuple)
            else:
                docmap.add(path_tuple, docid)
            if ICatalogable.providedBy(node) and catalog is not None:
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
    docmap = find_docmap(obj)
    if docmap is not None:
        path_tuple = resource_path_tuple(obj)
        docids = docmap.remove(path_tuple)
        if catalog is not None:
            for docid in docids:
                if docid in catalog.docids:
                    catalog.unindex_doc(docid)

@subscriber([Interface, IObjectModifiedEvent])
def object_modified(obj, event):
    """ Reindex a single piece of content (non-recursive); an
    ObjectModifed event subscriber """
    docmap = find_docmap(obj)
    if docmap is not None:
        path_tuple = resource_path_tuple(obj)
        docid = docmap.path_to_docid.get(path_tuple)
        if docid is None:
            object_added(obj, event)
            docid = getattr(obj, '__docid__')
        else:
            catalog = find_catalog(obj)
            if ICatalogable.providedBy(obj) and catalog is not None:
                catalog.reindex_doc(docid, obj)

