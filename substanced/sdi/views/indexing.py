from pyramid.view import view_defaults
from pyramid.httpexceptions import HTTPFound
from pyramid.session import check_csrf_token
from pyramid.util import LAST

from ...catalog import (
    catalog_view_factory_for, 
    CatalogViewWrapper,
    )
from ...content import find_services
from ...util import get_oid

from .. import mgmt_view

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
        tab_before=LAST, # try not to be the default tab, we're too obscure
        )
    def show(self):
        oid = get_oid(self.context)
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
        oid = get_oid(self.context)
        catalog_view_factory = self.catalog_view_factory_for(
            context, request.registry)
        if catalog_view_factory:
            wrapper = CatalogViewWrapper(context, catalog_view_factory)
            for catalog in find_services(context, 'catalog'):
                catalog.reindex_doc(oid, wrapper)
        request.sdiapi.flash_with_undo('Object reindexed', 'success')
        return HTTPFound(request.sdiapi.mgmt_url(self.context, '@@indexing'))
