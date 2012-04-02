import logging

import transaction

from zope.interface import directlyProvides

from repoze.catalog.catalog import Catalog as _Catalog

from pyramid.traversal import (
    find_resource,
    find_interface,
    )

from pyramid.threadlocal import get_current_registry

from ..interfaces import (
    ISearch,
    ICatalogSite,
    )

from .docmap import DocumentMap

logger = logging.getLogger(__name__)

def find_site(context):
    return find_interface(context, ICatalogSite)

def find_catalog(context):
    return getattr(find_site(context), 'catalog', None)

class Catalog(_Catalog):
    def __init__(self, site, family=None):
        _Catalog.__init__(self, family)
        directlyProvides(site, ICatalogSite)
        site.catalog = self
        self.site = site
        self.document_map = DocumentMap()

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
        for path, docid in self.document_map.path_to_docid.items():
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

    def resolver(self, docid):
        def path_for_docid(docid):
            return self.catalog.document_map.docid_to_path.get(docid)
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
