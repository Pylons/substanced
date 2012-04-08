import re

from pyramid.security import (
    Deny,
    Everyone,
    AllPermissionsList,
    NO_PERMISSION_REQUIRED,
    ALL_PERMISSIONS,
    )

from substanced.interfaces import ICatalogable
from substanced.service import find_service

from substanced.util import postorder

from . import mgmt_view

from .helpers import check_csrf_token

def get_workflow(*arg, **kw):
    return # XXX

def get_security_states(*arg, **kw):
    return [] # XXX

COMMA_WS = re.compile(r'[\s,]+')

ALL = AllPermissionsList()
NO_INHERIT = (Deny, Everyone, ALL)

def get_context_workflow(context):
    """
    If context is content and part of a workflow will return the workflow.
    Otherwise returns None.
    """
    return

@mgmt_view(name='acl_edit', permission='change acls', 
           renderer='templates/acl.pt', tab_title='Security')
def acl_edit_view(context, request):

    acl = original_acl = getattr(context, '__acl__', [])
    if acl and acl[-1] == NO_INHERIT:
        acl = acl[:-1]
        epilog = [NO_INHERIT]
    else:
        epilog = []

    if 'form.move_up' in request.POST:
        check_csrf_token(request)
        index = int(request.POST['index'])
        if index > 0:
            new = acl[:]
            new[index-1], new[index] = new[index], new[index-1]
            acl = new

    elif 'form.move_down' in request.POST:
        check_csrf_token(request)
        index = int(request.POST['index'])
        if index < len(acl) - 1:
            new = acl[:]
            new[index+1], new[index] = new[index], new[index+1]
            acl = new

    elif 'form.remove' in request.POST:
        check_csrf_token(request)
        index = int(request.POST['index'])
        new = acl[:]
        del new[index]
        acl = new

    elif 'form.add' in request.POST:
        check_csrf_token(request)
        verb = request.POST['verb']
        principal = request.POST['principal']
        principals = find_service(context, 'principals')
        principal_id = None
        if principal in principals['users']:
            principal_id = principals['users'][principal].__objectid__
        elif principal in principals['groups']:
            principal_id = principals['groups'][principal].__objectid__
        if principal_id is not None:
            permission = request.POST['permission']
            if permission == '-- ALL --':
                permissions = ALL_PERMISSIONS
            else:
                permissions = (permission,)
            new = acl[:]
            new.append((verb, principal_id, permissions))
            acl = new

    elif 'form.inherit' in request.POST:
        check_csrf_token(request)
        no_inherit = request.POST['inherit'] == 'disabled'
        if no_inherit:
            epilog = [NO_INHERIT]
        else:
            epilog = []

    elif 'form.security_state' in request.POST:
        check_csrf_token(request)
        new_state = request.POST['security_state']
        if new_state != 'CUSTOM':
            workflow = get_context_workflow(context)
            if hasattr(context, '__custom_acl__'):
                workflow.reset(context)
                del context.__custom_acl__
            workflow.transition_to_state(context, request, new_state)

    acl = acl + epilog

    if acl != original_acl:
        context.__custom_acl__ = acl # added so we can find customized obs later
        context.__acl__ = acl
        catalog = find_service(context, 'catalog')
        if catalog is not None:
            allowed = catalog.get('allowed')
            if allowed is not None:
                for node in postorder(context):
                    if ICatalogable.providedBy(node):
                        catalog.reindex_doc(node.__objectid__, node)

    workflow = get_context_workflow(context)
    if workflow is not None:
        if hasattr(context, '__custom_acl__'):
            security_state = 'CUSTOM'
            security_states = [s['name'] for s in
                               workflow.state_info(context, request)]
            security_states.insert(0, 'CUSTOM')
        else:
            security_state = workflow.state_of(context)
            security_states = [s['name'] for s in
                               get_security_states(workflow, context, request)]

    else:
        security_state = None
        security_states = None

    parent = context.__parent__
    parent_acl = []
    while parent is not None:
        p_acl = getattr(parent, '__acl__', ())
        stop = False
        for ace in p_acl:
            if ace == NO_INHERIT:
                stop = True
            else:
                parent_acl.append(ace)
        if stop:
            break
        parent = parent.__parent__

    local_acl = []
    inheriting = 'enabled'
    l_acl = getattr(context, '__acl__', ())
    objectmap = find_service(context, 'objectmap')
    for l_ace in l_acl:
        principal_id = l_ace[1]
        permissions = l_ace[2]
        if l_ace == NO_INHERIT:
            inheriting = 'disabled'
            break
        if permissions == ALL_PERMISSIONS:
            permissions = ('-- ALL --',)
        principal = objectmap.object_for(principal_id)
        if principal is None:
            pname = '<deleted principal>'
        else:
            pname = principal.__name__
            
        new_ace = (l_ace[0], pname, permissions)
        local_acl.append(new_ace)

    permissions = ['-- ALL --']
    introspector = request.registry.introspector
    for data in introspector.get_category('permissions'): 
        name = data['introspectable']['value']
        if name != NO_PERMISSION_REQUIRED:
            permissions.append(name)
    permissions.sort()

    return dict(
        parent_acl=parent_acl or (),
        local_acl=local_acl,
        permissions=permissions,
        inheriting=inheriting,
        security_state=security_state,
        security_states=security_states)

