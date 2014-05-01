from ..event import subscribe_acl_modified

from . import find_objectmap

@subscribe_acl_modified()
def acl_modified(event):
    """ When the ACL of any object is modified, fix the objectmap's
    path_to_acl mapping. """
    objectmap = find_objectmap(event.object)

    if objectmap is not None: # object might not yet be seated
        objectmap.set_acl(event.object, event.new_acl)

