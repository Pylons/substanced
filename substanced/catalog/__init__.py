import logging

import transaction

from BTrees.IIBTree import IITreeSet

from zope.interface import directlyProvides

from repoze.catalog.catalog import Catalog as _Catalog

from pyramid.traversal import (
    find_resource,
    find_interface,
    )

from ..docmap import find_docmap

from pyramid.threadlocal import get_current_registry

from ..interfaces import (
    ISearch,
    ICatalogSite,
    )

logger = logging.getLogger(__name__)

def find_site(context):
    return find_interface(context, ICatalogSite)

def find_catalog(context):
    return getattr(find_site(context), 'catalog', None)

class Catalog(_Catalog):
    def __init__(self, site, family=None):
        _Catalog.__init__(self, family)
        site.catalog = self
        self.site = site
        self.docids = IITreeSet()

    def clear(self):
        """ Clear all indexes in this catalog. """
        _Catalog.clear(self)
        self.docids = IITreeSet()

    def index_doc(self, docid, obj):
        """Register the document represented by ``obj`` in indexes of
        this catalog using docid ``docid``."""
        _Catalog.index_doc(self, docid, obj)
        self.docids.insert(docid)

    def unindex_doc(self, docid):
        """Unregister the document id from indexes of this catalog."""
        _Catalog.unindex_doc(self, docid)
        try:
            self.docids.remove(docid)
        except KeyError:
            pass

    def reindex_doc(self, docid, obj):
        """ Reindex the document referenced by docid using the object
        passed in as ``obj`` (typically just does the equivalent of
        ``unindex_doc``, then ``index_doc``, but specialized indexes
        can override the method that this API calls to do less work. """
        _Catalog.reindex_doc(self, docid)
        if not docid in self.docids:
            self.docids.insert(docid)

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
        docmap = find_docmap(self.site)
        for docid in self.docids:
            path = docmap.docid_to_path.get(docid)
            upath = u'/'.join(path)
            if path_re is not None and path_re.match(upath) is None:
                continue
            output and output('reindexing %s' % upath)
            try:
                resource = find_resource(self.site, path)
            except KeyError:
                output and output('error: %s not found' % upath)
                continue

            if indexes is None:
                self.reindex_doc(docid, resource)
            else:
                for index in indexes:
                    self[index].reindex_doc(docid, resource)
            if i % commit_interval == 0: # pragma: no cover
                commit_or_abort()
            i+=1
        commit_or_abort()

    def refresh(self, output=None, registry=None):
        output and output('refreshing indexes')

        if registry is None:
            registry = get_current_registry()

        indexes = getattr(registry, '_pyramid_catalog_indexes', {})
        
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
        self.catalog = find_catalog(self.context)
        self.docmap = find_docmap(self.context)

    def resolver(self, docid):
        def path_for_docid(docid):
            return self.docmap.docid_to_path.get(docid)
        path = path_for_docid(docid)
        if path is None:
            return None
        try:
            return find_resource(self.context, path)
        except KeyError:
            logger.warn('Resource missing: %s' % (path,))
            return None
        
    def query(self, q, **kw):
        num, docids = self.catalog.query(q, **kw)
        return num, docids, self.resolver

    def search(self, **kw):
        num, docids = self.catalog.search(**kw)
        return num, docids, self.resolver
    
def _add_catalog_index(config, name, index): # pragma: no cover
    def register():
        indexes = getattr(config.registry, '_pyramid_catalog_indexes', {})
        indexes[name] = index
        config.registry._pyramid_catalog_indexes = indexes
    config.action(('catalog-index', name), callable=register)

def includeme(config): # pragma: no cover
    from zope.interface import Interface
    config.registry.registerAdapter(Search, (Interface,), ISearch)
    config.add_directive('add_catalog_index', _add_catalog_index)
    config.scan('substanced.catalog.subscribers')
    
