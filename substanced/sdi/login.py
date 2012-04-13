from pyramid.httpexceptions import (
    HTTPForbidden,
    HTTPFound
    )
from pyramid.security import (
    remember,
    forget,
    )

from . import (
    mgmt_view,
    check_csrf_token,
    )
from ..service import find_service
from ..util import oid_of

@mgmt_view(name='login', renderer='templates/login.pt', tab_condition=False)
@mgmt_view(renderer='templates/login.pt', context=HTTPForbidden, 
           tab_condition=False)
def login(context, request):
    login_url = request.mgmt_path(request.context, 'login')
    referrer = request.url
    if login_url in referrer:
        # never use the login form itself as came_from
        referrer = request.mgmt_path(request.root) 
    came_from = request.session.setdefault('came_from', referrer)
    login = ''
    password = ''
    if 'form.submitted' in request.params:
        check_csrf_token(request)
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
