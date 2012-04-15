from pyramid.httpexceptions import HTTPFound

from pyramid.view import view_defaults
from pyramid_zodbconn import get_connection

from ..interfaces import ISite
from ..sdi import mgmt_view

@view_defaults(
    name='manage_db',
    context=ISite,
    renderer='templates/manage_db.pt',
    permission='manage database')
class ManageDatabase(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request

    @mgmt_view(request_method='GET', tab_title='Manage DB')
    def view(self):
        return {}

    @mgmt_view(request_method='POST', request_param='pack', check_csrf=True)
    def pack(self):
        conn = get_connection(self.request)
        try:
            days = int(self.request.POST['days'])
        except:
            self.request.session.flash('Invalid number of days', 'error')
        conn.db().pack(days=days)
        self.request.session.flash('Database packed to %s days' % days)
        return HTTPFound(location=self.request.mgmt_path(
            self.context, '@@manage_db'))

