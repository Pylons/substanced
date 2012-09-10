from .objectmap import ObjectMap
from .folder import Folder
from .folder import Services

def make_site():
    context = Folder()
    ObjectMap(context)
    users = Folder()
    groups = Folder()
    principals = Folder()
    principals['groups'] = groups
    principals['users'] = users
    services = Services()
    context.add('__services__', services, reserved_names=())
    services['principals'] = principals
    return context

