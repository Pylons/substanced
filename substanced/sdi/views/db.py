import json

from pyramid_zodbconn import get_connection

from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_defaults

from .. import mgmt_view

@view_defaults(
    physical_path='/',
    name='manage_db',
    renderer='templates/db.pt',
    permission='sdi.manage-database'
    )
class ManageDatabase(object):
    get_connection = staticmethod(get_connection)
    def __init__(self, context, request):
        self.context = context
        self.request = request

    @mgmt_view(request_method='GET', tab_title='Manage DB')
    def view(self):
        conn = self.get_connection(self.request)
        db = conn.db()
        am = db.getActivityMonitor()

        data_connections = []
        data_object_stores = []
        data_object_loads = []

        if am:
            # we multiply datetime by 1000 to get JavaScript representatin of
            # unix timestamp
            # TODO: add timezone support
            for data in am.getActivityAnalysis():
                data_connections.append(
                    [int(data['end']*1000), data['connections']])
                data_object_stores.append(
                    [int(data['end']*1000), data['stores']])
                data_object_loads.append(
                    [int(data['end']*1000), data['loads']])
        return dict(
            am=am,
            db=db,
            conn=conn,
            data_connections=json.dumps(data_connections),
            data_object_stores=json.dumps(data_object_stores),
            data_object_loads=json.dumps(data_object_loads),
            )

    @mgmt_view(request_method='POST', request_param='pack', check_csrf=True)
    def pack(self):
        try:
            days = int(self.request.POST['days'])
        except:
            self.request.session.flash('Invalid number of days', 'error')
            raise HTTPFound(location=self.request.sdiapi.mgmt_path(
                self.context, '@@manage_db'))
        conn = self.get_connection(self.request)
        conn.db().pack(days=days)
        self.request.session.flash('Database packed to %s days' % days)
        return HTTPFound(location=self.request.sdiapi.mgmt_path(
            self.context, '@@manage_db'))

    @mgmt_view(request_method='POST', request_param='flush_cache',
               check_csrf=True)
    def flush_cache(self):
        conn = self.get_connection(self.request)
        conn.db().cacheMinimize()
        self.request.session.flash('Database flushed cache')
        return HTTPFound(location=self.request.sdiapi.mgmt_path(
            self.context, '@@manage_db'))

