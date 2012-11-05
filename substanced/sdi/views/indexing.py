from pyramid.view import view_defaults
from pyramid.httpexceptions import HTTPFound
from pyramid.session import check_csrf_token

from ...catalog import (
    catalog_view_factory_for, 
    CatalogViewWrapper,
    )
from ...content import find_services
from ...util import oid_of

from .. import (
    mgmt_view,
    MIDDLE
    )

@view_defaults(
    catalogable=True,
    name='indexing',
    permission='sdi.manage-catalog',
    )
class IndexingView(object):

    catalog_view_factory_for = staticmethod(catalog_view_factory_for) # testing

    def __init__(self, context, request):
        self.context = context
        self.request = request
    
    @mgmt_view(
        renderer='templates/indexing.pt',
        tab_title='Indexing',
        tab_after=MIDDLE, # try not to be the default tab, we're too obscure
        )
    def show(self):
        oid = oid_of(self.context)
        catalogs = []
        for catalog in find_services(self.context, 'catalog'):
            indexes = []
            catalogs.append((catalog, indexes))
            for index in catalog.values():
                docrepr = index.document_repr(oid, '(not indexed)')
                indexes.append({'index':index, 'value':docrepr})
        return {'catalogs':catalogs}

    @mgmt_view(request_method='POST', tab_title=None)
    def reindex(self):
        context = self.context
        request = self.request
        check_csrf_token(request)
        oid = oid_of(self.context)
        catalog_view_factory = self.catalog_view_factory_for(
            context, request.registry)
        if catalog_view_factory:
            wrapper = CatalogViewWrapper(context, catalog_view_factory)
            for catalog in find_services(context, 'catalog'):
                catalog.reindex_doc(oid, wrapper)
        request.flash_with_undo('Object reindexed', 'success')
        return HTTPFound(request.mgmt_url(self.context, '@@indexing'))
