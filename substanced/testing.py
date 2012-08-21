from .objectmap import ObjectMap
from .folder import Folder
from .folder import Services

def make_site():
    context = Folder()
    objectmap = ObjectMap()
    users = Folder()
    groups = Folder()
    principals = Folder()
    principals['groups'] = groups
    principals['users'] = users
    services = Services()
    context.add('__services__', services, reserved_names=())
    services['principals'] = principals
    services['objectmap'] = objectmap
    return context

