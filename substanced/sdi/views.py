from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPFound
    )

from pyramid.session import check_csrf_token

from pyramid.security import (
    remember,
    forget,
    )

from . import (
    mgmt_view,
    sdi_mgmt_views,
    sdi_add_views,
    )

import json

from pyramid.view import view_defaults
from pyramid_zodbconn import get_connection

from ..content import find_service
from ..util import oid_of
from ..interfaces import IFolder

@mgmt_view(name='login', renderer='templates/login.pt', tab_condition=False)
@mgmt_view(renderer='templates/login.pt', context=HTTPForbidden, 
           tab_condition=False)
def login(context, request):
    login_url = request.mgmt_path(request.context, 'login')
    referrer = request.url
    if login_url in referrer: # pragma: no cover
        # never use the login form itself as came_from
        referrer = request.mgmt_path(request.root) 
    came_from = request.session.setdefault('came_from', referrer)
    login = ''
    password = ''
    if 'form.submitted' in request.params:
        try:
            check_csrf_token(request)
        except:
            request.session.flash('Failed login (CSRF)', 'error')
        else:
            login = request.params['login']
            password = request.params['password']
            principals = find_service(context, 'principals')
            users = principals['users']
            user = users.get(login)
            if user is not None and user.check_password(password):
                headers = remember(request, oid_of(user))
                request.session.flash('Welcome!', 'success')
                return HTTPFound(location = came_from, headers = headers)
            request.session.flash('Failed login', 'error')

    return dict(
        url = request.mgmt_path(request.root, 'login'),
        came_from = came_from,
        login = login,
        password = password,
        )

@mgmt_view(name='logout', tab_condition=False)
def logout(request):
    headers = forget(request)
    return HTTPFound(location = request.mgmt_path(request.context),
                     headers = headers)

class ManagementViews(object):
    # these defined as staticmethods only for test overriding
    sdi_mgmt_views = staticmethod(sdi_mgmt_views)
    sdi_add_views = staticmethod(sdi_add_views)
    
    def __init__(self, context, request):
        self.context = context
        self.request = request

    @mgmt_view(tab_condition=False)
    @mgmt_view(name='manage_main', tab_condition=False)
    def manage_main(self):
        request = self.request
        view_data = self.sdi_mgmt_views(request)
        if not view_data:
            request.session['came_from'] = request.url
            return HTTPFound(
                location=request.mgmt_path(request.root, '@@login')
                )
        view_name = view_data[0]['view_name']
        return HTTPFound(
            location=request.mgmt_path(request.context, '@@%s' % view_name)
            )

    @mgmt_view(context=IFolder, name='add', tab_title='Add', 
               permission='sdi.manage-contents', renderer='templates/add.pt',
               tab_condition=False)
    def add_content(self):
        views = self.sdi_add_views(self.request, self.context)
        if len(views) == 1:
            return HTTPFound(location=views[0]['url'])
        return {'views':views}

@view_defaults(
    physical_path='/',
    name='manage_db',
    renderer='templates/manage_db.pt',
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
            raise HTTPFound(location=self.request.mgmt_path(
                self.context, '@@manage_db'))
        conn = self.get_connection(self.request)
        conn.db().pack(days=days)
        self.request.session.flash('Database packed to %s days' % days)
        return HTTPFound(location=self.request.mgmt_path(
            self.context, '@@manage_db'))

    @mgmt_view(request_method='POST', request_param='flush_cache',
               check_csrf=True)
    def flush_cache(self):
        conn = self.get_connection(self.request)
        conn.db().cacheMinimize()
        self.request.session.flash('Database flushed cache')
        return HTTPFound(location=self.request.mgmt_path(
            self.context, '@@manage_db'))
