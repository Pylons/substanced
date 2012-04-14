import logging

import transaction

import BTrees

from repoze.catalog.catalog import Catalog as _Catalog

from pyramid.threadlocal import get_current_registry
from pyramid.traversal import resource_path

from ..interfaces import (
    ISearch,
    ICatalog,
    )

from ..content import content
from ..service import find_service

logger = logging.getLogger(__name__) # API

@content(ICatalog, icon='icon-search')
class Catalog(_Catalog):
    family = BTrees.family32
    def __init__(self, family=None):
        _Catalog.__init__(self, family)
        self.objectids = self.family.IF.TreeSet()

    def clear(self):
        """ Clear all indexes in this catalog. """
        _Catalog.clear(self)
        self.objectids = self.family.IF.TreeSet()

    def index_doc(self, docid, obj):
        """Register the document represented by ``obj`` in indexes of
        this catalog using objectid ``docid``."""
        _Catalog.index_doc(self, docid, obj)
        self.objectids.insert(docid)

    def unindex_doc(self, docid):
        """Unregister the document represented by docid from indexes of
        this catalog."""
        _Catalog.unindex_doc(self, docid)
        try:
            self.objectids.remove(docid)
        except KeyError:
            pass

    def reindex_doc(self, docid, obj):
        """ Reindex the document referenced by docid using the object
        passed in as ``obj`` (typically just does the equivalent of
        ``unindex_doc``, then ``index_doc``, but specialized indexes
        can override the method that this API calls to do less work. """
        _Catalog.reindex_doc(self, docid, obj)
        if not docid in self.objectids:
            self.objectids.insert(docid)

    def reindex(self, path_re=None, commit_interval=200, 
                dry_run=False, output=None, transaction=transaction, 
                indexes=None, registry=None):

        def commit_or_abort():
            if dry_run:
                output and output('*** aborting ***')
                transaction.abort()
            else:
                output and output('*** committing ***')
                transaction.commit()

        self.refresh(output=output, registry=registry)
        
        commit_or_abort()

        if indexes is not None:
            output and output('reindexing only indexes %s' % str(indexes))

        i = 1
        objectmap = find_service(self, 'objectmap')
        for objectid in self.objectids:
            resource = objectmap.object_for(objectid)
            if resource is None:
                path = objectmap.path_for(objectid)
                if path is None:
                    output and output(
                        'error: no path for objectid %s in object map' % 
                        objectid)
                    continue
                upath = u'/'.join(path)
                output and output('error: object at path %s not found' % upath)
                continue
            path = resource_path(resource)
            if path_re is not None and path_re.match(path) is None:
                continue
            output and output('reindexing %s' % path)

            if indexes is None:
                self.reindex_doc(objectid, resource)
            else:
                for index in indexes:
                    self[index].reindex_doc(objectid, resource)
            if i % commit_interval == 0: # pragma: no cover
                commit_or_abort()
            i+=1
        commit_or_abort()

    def refresh(self, output=None, registry=None):
        output and output('refreshing indexes')

        if registry is None:
            registry = get_current_registry()

        indexes = getattr(registry, '_substanced_indexes', {})
        
        # add mentioned indexes
        for name, index in indexes.items():
            if not name in self:
                self[name] = index
                output and output('added %s index' % (name,))

        # remove unmentioned indexes
        todel = set()
        for name in self:
            if not name in indexes:
                todel.add(name)
        for name in todel:
            del self[name]
            output and output('removed %s index' % (name,))

        output and output('refreshed')

class Search(object):
    """ Catalog query helper """
    def __init__(self, context):
        self.context = context
        self.catalog = find_service(self.context, 'catalog')
        self.objectmap = find_service(self.context, 'objectmap')

    def resolver(self, objectid):
        resource = self.objectmap.object_for(objectid)
        if resource is None:
            logger.warn('Resource for objectid %s missing' % (objectid,))
        return resource
        
    def query(self, q, **kw):
        num, objectids = self.catalog.query(q, **kw)
        return num, objectids, self.resolver

    def search(self, **kw):
        num, objectids = self.catalog.search(**kw)
        return num, objectids, self.resolver
    
def _add_catalog_index(config, name, index): # pragma: no cover
    def register():
        indexes = getattr(config.registry, '_substanced_indexes', {})
        indexes[name] = index
        config.registry._substanced_indexes = indexes
    config.action(('catalog-index', name), callable=register)

class _catalog_request_api(object):
    Search = Search
    def __init__(self, request):
        self.request = request
        self.context = request.context

class query_catalog(_catalog_request_api):
    def __call__(self, *arg, **kw):
        return self.Search(self.context).query(*arg, **kw)

class search_catalog(_catalog_request_api):
    def __call__(self, **kw):
        return self.Search(self.context).search(**kw)

def includeme(config): # pragma: no cover
    from zope.interface import Interface
    config.registry.registerAdapter(Search, (Interface,), ISearch)
    config.add_directive('add_catalog_index', _add_catalog_index)
    config.set_request_property(query_catalog, reify=True)
    config.set_request_property(search_catalog, reify=True)
    config.scan('substanced.catalog')
    
