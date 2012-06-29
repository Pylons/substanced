from pyramid.security import Allow

from ..event import (
    subscribe_added,
    subscribe_will_be_removed,
    )

from ..interfaces import (
    IUser,
    IPrincipal,
)

from ..service import find_service
from ..util import oid_of

from . import UserToPasswordReset

@subscribe_added(IUser)
def user_added(event):
    """ Give each user permission to change their own password."""
    user = event.object
    user.__acl__ = [(Allow, oid_of(user), ('sdi.view', 'sdi.change-password'))]

@subscribe_will_be_removed(IUser)
def user_will_be_removed(event):
    """ Remove all password reset objects associated with a user when the user
    is removed """
    user = event.object
    if event.moving: # it's not really being removed
        return
    objectmap = find_service(user, 'objectmap')
    if objectmap is not None:
        resets = objectmap.targets(user, UserToPasswordReset)
        for reset in resets:
            reset.commit_suicide()

@subscribe_added(IPrincipal)
def principal_added(event):
    """ Prevent same-named users and groups from being added to the system.
    An :class:`substanced.event.IObjectAdded` event subscriber."""
    # disallow same-named groups and users for human sanity (not because
    # same-named users and groups are disallowed by the system)
    principal = event.object
    principal_name = principal.__name__
    principals = find_service(principal, 'principals')
    
    if IUser.providedBy(principal):
        # its a user
        groups = principals['groups']
        if principal_name in groups:
            raise ValueError(
                'Cannot add a user with a login name the same as the '
                'group name %s' % principal_name
                )
    else:
        # its a group
        users = principals['users']
        if principal_name in users:
            raise ValueError(
                'Cannot add a group with a name the same as the '
                'user with the login name %s' % principal_name
            )
    
