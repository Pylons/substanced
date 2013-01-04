from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPFound
    )
from pyramid.session import check_csrf_token
from pyramid.security import (
    remember,
    forget,
    Authenticated,
    NO_PERMISSION_REQUIRED,
    )

from ...util import (
    get_oid,
    find_service,
    )

from .. import mgmt_view

@mgmt_view(
    name='login',
    renderer='templates/login.pt',
    tab_condition=False,
    permission=NO_PERMISSION_REQUIRED
    )
@mgmt_view(
    renderer='templates/login.pt',
    context=HTTPForbidden,
    permission=NO_PERMISSION_REQUIRED,
    tab_condition=False
    )
@mgmt_view(
    renderer='templates/forbidden.pt',
    context=HTTPForbidden,
    permission=NO_PERMISSION_REQUIRED,
    effective_principals=Authenticated,
    tab_condition=False
    )
def login(context, request):
    login_url = request.sdiapi.mgmt_path(request.context, 'login')
    referrer = request.url
    if login_url in referrer: # pragma: no cover
        # never use the login form itself as came_from
        referrer = request.sdiapi.mgmt_path(request.root) 
    came_from = request.session.setdefault('sdi.came_from', referrer)
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
                request.session.pop('sdi.came_from', None)
                headers = remember(request, get_oid(user))
                return HTTPFound(location = came_from, headers = headers)
            request.session.flash('Failed login', 'error')

    return dict(
        url = request.sdiapi.mgmt_path(request.root, 'login'),
        came_from = came_from,
        login = login,
        password = password,
        )

@mgmt_view(
    name='logout',
    tab_condition=False,
    permission=NO_PERMISSION_REQUIRED
    )
def logout(request):
    headers = forget(request)
    return HTTPFound(location = request.sdiapi.mgmt_path(request.context),
                     headers = headers)
