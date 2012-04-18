from pyramid.events import subscriber
from pyramid.security import Allow

from ..interfaces import (
    IUser,
    IObjectAdded,
)

@subscriber([IUser, IObjectAdded])
def on_add(obj, event):
    """ Give each user permission to change their own password."""
    user = event.object
    user.__acl__ = [(Allow, user.__objectid__,
                     ('sdi.view', 'sdi.change-password'))]
