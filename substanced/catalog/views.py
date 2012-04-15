from pyramid.httpexceptions import HTTPFound

from pyramid.view import view_defaults

from ..interfaces import ICatalog
from ..sdi import (
    mgmt_view,
    check_csrf_token,
    )

@view_defaults(
    name='manage_catalog',
    context=ICatalog,
    renderer='templates/manage_catalog.pt',
    permission='manage catalog')
class ManageCatalog(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request

    @mgmt_view(request_method='GET', tab_title='Manage')
    def GET(self):
        cataloglen = len(self.context.objectids)
        return dict(cataloglen=cataloglen)

    @mgmt_view(request_method='POST')
    def POST(self):
        check_csrf_token(self.request)
        location=self.request.mgmt_path(self.context, '@@manage_catalog')
        if 'reindex' in self.request.POST:
            self.context.reindex()
            self.request.session.flash('Catalog reindexed')
            return HTTPFound(location=location)
        elif 'refresh' in self.request.POST:
            self.context.refresh(registry=self.request.registry)
            self.request.session.flash('Catalog refreshed')
            return HTTPFound(location=location)
        else:
            self.request.session.flash('Unknown command', 'error')
            return HTTPFound(location=location)

