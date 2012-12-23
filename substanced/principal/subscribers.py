from pyramid.security import Allow

from ..event import (
    subscribe_added,
    subscribe_will_be_removed,
    subscribe_acl_modified,
    )

from ..interfaces import (
    IUser,
    IPrincipal,
)

from ..objectmap import find_objectmap
from ..util import (
    get_oid,
    postorder,
    set_acl,
    find_service,
    )

from ..interfaces import (
    UserToPasswordReset,
    PrincipalToACLBearing,
    )

@subscribe_added(IUser)
def user_added(event):
    """ Give each user permission to change their own password."""
    if event.loading: # fbo dump/load
        return
    user = event.object
    registry = event.registry
    set_acl(
        user,
        [(Allow, get_oid(user), ('sdi.view', 'sdi.change-password'))],
        registry=registry,
        )

@subscribe_will_be_removed(IUser)
def user_will_be_removed(event):
    """ Remove all password reset objects associated with a user when the user
    is removed """
    if event.moving is not None: # it's not really being removed
        return
    if event.loading: # fbo dump/load
        return
    user = event.object
    objectmap = find_objectmap(user)
    if objectmap is not None:
        resets = objectmap.targets(user, UserToPasswordReset)
        for reset in resets:
            reset.commit_suicide()

@subscribe_added(IPrincipal)
def principal_added(event):
    """ Prevent same-named users and groups from being added to the system.
    An :class:`substanced.event.IObjectAdded` event subscriber."""
    if event.loading: # fbo dump/load
        return

    # disallow same-named groups and users for human sanity (not because
    # same-named users and groups are disallowed by the system)
    principal = event.object
    principal_name = principal.__name__
    principals = find_service(principal, 'principals')

    if IUser.providedBy(principal):
        # it's a user
        groups = principals['groups']
        if principal_name in groups:
            raise ValueError(
                'Cannot add a user with a login name the same as the '
                'group name %s' % principal_name
                )
    else:
        # it's a group
        users = principals['users']
        if principal_name in users:
            raise ValueError(
                'Cannot add a group with a name the same as the '
                'user with the login name %s' % principal_name
            )

def _referenceable_principals(acl):
    result = set()
    for ace in (acl or ()):
        principal_id = ace[1]
        if isinstance(principal_id, (int, long, tuple)):
            result.add(principal_id)
    return result

@subscribe_added()
def acl_maybe_added(event):
    if event.moving is not None or event.loading:
        return False # meaningful only to tests

    obj = event.object
    objectmap = find_objectmap(obj)

    if objectmap is not None:
        for resource in postorder(obj):
            acl = getattr(resource, '__acl__', None)
            if acl is not None:
                for princid in _referenceable_principals(acl):
                    objectmap.connect(
                        princid, resource, PrincipalToACLBearing
                        )

@subscribe_acl_modified()
def acl_modified(event):
    """ When an object bearing an ACL is modified or added, using the object
    map, form relationships between the principal objects it names and the
    ACL-bearing object.  Disallow a principal involved in any such relationship
    from being deleted using reference integrity."""
    objectmap = find_objectmap(event.object)

    if objectmap is not None:

        old_principals = _referenceable_principals(event.old_acl)
        new_principals = _referenceable_principals(event.new_acl)

        principals_removed = old_principals.difference(new_principals)
        principals_added = new_principals.difference(old_principals)

        for princid in principals_removed:
            objectmap.disconnect(
                princid,
                event.object,
                PrincipalToACLBearing
                )

        for princid in principals_added:
            objectmap.connect(
                princid,
                event.object,
                PrincipalToACLBearing
                )
