import logging

import transaction

from zope.interface import directlyProvides

from repoze.catalog.document import DocumentMap
from repoze.catalog.catalog import Catalog

from pyramid.traversal import (
    find_resource,
    find_interface,
    )

from ..interfaces import (
    ISearch,
    ICatalogSite,
    )

logger = logging.getLogger(__name__)

def find_site(context):
    return find_interface(context, ICatalogSite)

def find_catalog(context):
    return getattr(find_site(context), 'catalog', None)

class CatalogManager(object):
    def __init__(self, site, registry, output=None):
        self.site = site
        self.registry = registry
        self.output = output

    def reindex(self, path_re=None, commit_interval=200, 
                dry_run=False, output=None, transaction=transaction, 
                indexes=None):

        output = self.output
        
        def commit_or_abort():
            if dry_run:
                output and output('*** aborting ***')
                transaction.abort()
            else:
                output and output('*** committing ***')
                transaction.commit()

        self.refresh()
        
        catalog = self.site.catalog

        commit_or_abort()

        if indexes is not None:
            output and output('reindexing only indexes %s' % str(indexes))

        i = 1
        for path, docid in catalog.document_map.path_to_docid.items():
            if path_re is not None and path_re.match(path) is None:
                continue
            output and output('reindexing %s' % path)
            try:
                model = find_resource(self.site, path)
            except KeyError:
                output and output('error: %s not found' % path)
                continue

            if indexes is None:
                catalog.reindex_doc(docid, model)
            else:
                for index in indexes:
                    catalog[index].reindex_doc(docid, model)
            if i % commit_interval == 0:
                commit_or_abort()
            i+=1
        commit_or_abort()

    def refresh(self, reset=False):
        self.output and self.output('refreshing indexes')
        catalog = find_catalog(self.site)

        if catalog is None:
            # create a catalog
            self.site.catalog = Catalog()
            self.site.catalog.document_map = DocumentMap()
            directlyProvides(self.site, ICatalogSite)

        indexes = getattr(self.registry, '_pyramid_catalog_indexes', {})
        
        # add mentioned indexes
        for name, index in indexes.items():
            if reset:
                try:
                    del catalog[name]
                except KeyError:
                    pass
            if not name in catalog:
                catalog[name] = index

        # remove unmentioned indexes
        for name in catalog:
            if name not in indexes:
                del catalog[name]

        self.output('refreshed')

class Search(object):
    """ Catalog query helper """
    def __init__(self, context):
        self.context = context
        self.catalog = find_catalog(self.context)

    def __call__(self, q, **kw):
        num, docids = self.catalog.query(q, **kw)
        def path_for_docid(docid):
            return self.catalog.document_map.docid_to_path.get(docid)
        def resolver(docid):
            path = path_for_docid(docid)
            if path is None:
                return None
            try:
                return find_resource(self.context, path)
            except KeyError:
                logger and logger.warn('Model missing: %s' % path)
                return None
        return num, docids, resolver

def add_catalog_index(config, name, index):
    def register():
        # each index needs to participate in conflict resolution
        indexes = getattr(config, '_catalog_indexes', {})
        indexes[name] = index
        config._catalog_indexes = indexes
    config.action(('catalog-index', name), callable=register)

def includeme(config):
    from zope.interface import Interface
    from repoze.catalog.indexes.path2 import CatalogPathIndex2
    from .discriminators import get_path
    config.registry.registerAdapter(Search, (Interface,), ISearch)
    config.add_directive('add_catalog_index', add_catalog_index)
    config.add_catalog_index('catalog_path', CatalogPathIndex2(get_path))
