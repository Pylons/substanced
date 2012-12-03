import logging

from pyramid.security import (
    NO_PERMISSION_REQUIRED,
    ALL_PERMISSIONS,
    Deny,
    Everyone,
    Authenticated,
    )
from pyramid.session import check_csrf_token

from ...objectmap import find_objectmap
from ...util import (
    get_oid,
    get_all_permissions,
    set_acl,
    find_service,
    )

from .. import mgmt_view

logger = logging.getLogger(__name__)

NO_INHERIT = (Deny, Everyone, ALL_PERMISSIONS)

@mgmt_view(name='acl_edit', permission='sdi.change-acls', 
           renderer='templates/acl.pt', tab_title='Security')
def acl_edit_view(context, request):
    principal_service = find_service(context, 'principals')
    objectmap = find_objectmap(context)
    registry = request.registry

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
        request.sdiapi.flash_with_undo('ACE moved up')

    elif 'form.move_down' in request.POST:
        check_csrf_token(request)
        index = int(request.POST['index'])
        if index < len(acl) - 1:
            new = acl[:]
            new[index+1], new[index] = new[index], new[index+1]
            acl = new
        request.sdiapi.flash_with_undo('ACE moved down')

    elif 'form.remove' in request.POST:
        check_csrf_token(request)
        index = int(request.POST['index'])
        new = acl[:]
        del new[index]
        acl = new
        request.sdiapi.flash_with_undo('ACE removed')

    elif 'form.add' in request.POST:
        check_csrf_token(request)
        verb = request.POST['verb']
        principal_id_str = request.POST['principal']
        if principal_id_str in (Everyone, Authenticated):
            principal_id = principal_id_str
        else:
            try:
                principal_id = int(principal_id_str)
            except ValueError:
                principal_id = None
                
        if principal_id is None:
            request.session.flash('No principal selected', 'error')
            
        else:
            if principal_id not in (Everyone, Authenticated):
                if objectmap.object_for(principal_id) is None:
                    request.session.flash(
                        'Unknown user or group when adding ACE',
                        'error')
                    principal_id = None
                    
            if principal_id is not None:
                permissions = request.POST.getall('permissions')
                if not permissions:
                    permissions = ()
                if '-- ALL --' in permissions:
                    permissions = ALL_PERMISSIONS
                new = acl[:]
                new.append((verb, principal_id, permissions))
                acl = new
                request.sdiapi.flash_with_undo('New ACE added')
                
    elif 'form.inherit' in request.POST:
        check_csrf_token(request)
        no_inherit = request.POST['inherit'] == 'disabled'
        if no_inherit:
            epilog = [NO_INHERIT]
            request.sdiapi.flash_with_undo('ACL will *not* inherit from parent')
        else:
            epilog = []
            request.sdiapi.flash_with_undo('ACL will inherit from parent')

    acl = acl + epilog

    if acl != original_acl:
        set_acl(context, acl, registry=registry)

    parent = context.__parent__
    parent_acl = []

    def get_principal_name(principal_id):
        if principal_id  in (Everyone, Authenticated):
            pname = principal_id
        else:
            principal = objectmap.object_for(principal_id)
            if principal is None:
                pname = '<deleted principal>'
            else:
                pname = principal.__name__
        return pname
        
    while parent is not None:
        p_acl = getattr(parent, '__acl__', ())
        stop = False
        for ace in p_acl:
            if ace == NO_INHERIT:
                stop = True
            else:
                principal_id = ace[1]
                pname = get_principal_name(principal_id)
                if ace[2] == ALL_PERMISSIONS:
                    perms =  ('-- ALL --',)
                else:
                    perms = ace[2]
                if not hasattr(perms, '__iter__'):
                    perms = (perms,)
                new_ace = (ace[0], pname, perms)
                parent_acl.append(new_ace)
        if stop:
            break
        parent = parent.__parent__

    local_acl = []
    inheriting = 'enabled'
    l_acl = getattr(context, '__acl__', ())
    for l_ace in l_acl:
        principal_id = l_ace[1]
        permissions = l_ace[2]
        if l_ace == NO_INHERIT:
            inheriting = 'disabled'
            break
        if permissions == ALL_PERMISSIONS:
            permissions = ('-- ALL --',)
        if not hasattr(permissions, '__iter__'):
            permissions = (permissions,)
        pname = get_principal_name(principal_id)
        new_ace = (l_ace[0], pname, permissions)
        local_acl.append(new_ace)

    permissions = set(['-- ALL --'])
    registered_permissions = get_all_permissions(registry)
    for name in registered_permissions:
        if name != NO_PERMISSION_REQUIRED:
            permissions.add(name)
    permissions = list(permissions)
    permissions.sort()

    users = principal_service['users'].values()
    users = [ (get_oid(user), user.__name__) for user in users ]
    groups = principal_service['groups'].values()
    groups = [ (get_oid(group), group.__name__) for group in groups ]
    groups = [ (Everyone, Everyone), (Authenticated, Authenticated) ] + groups

    return dict(
        parent_acl=parent_acl or (),
        local_acl=local_acl,
        permissions=permissions,
        inheriting=inheriting,
        users=users,
        groups=groups,
        )
