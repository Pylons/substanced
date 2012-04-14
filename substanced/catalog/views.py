from pyramid.httpexceptions import HTTPFound

from logging import getLogger

from pyramid.view import view_defaults

from ..interfaces import ICatalog
from ..sdi import (
    mgmt_view,
    check_csrf_token,
    )

logger = getLogger(__name__)

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
        self.context.reindex(output=logger.info)
        self.request.session.flash('Catalog reindexed')
        return HTTPFound(location=self.request.mgmt_path(
            self.context, '@@manage_catalog'))

