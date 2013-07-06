from substanced.interfaces import IUser

from substanced.event import subscribe_will_be_removed
from substanced.util import find_objectmap

from . import (
    UserToLock,
    WriteLock,
    )

@subscribe_will_be_removed()
def object_will_be_removed(event):
    """ Remove all lock objects associated with an object and/or user when
    it/he is removed"""
    if event.moving is not None: # it's not really being removed
        return
    if event.loading: # fbo dump/load
        return
    resource = event.object
    objectmap = find_objectmap(resource)
    if objectmap is not None:
        # might be None if resource is a broken object
        if IUser.providedBy(resource):
            locks = objectmap.targets(resource, UserToLock)
            for lock in locks:
                lock.commit_suicide()
        locks = objectmap.targets(resource, WriteLock)
        for lock in locks:
            lock.commit_suicide()
