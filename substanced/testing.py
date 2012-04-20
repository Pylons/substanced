from .objectmap import ObjectMap
from .folder import Folder

def make_site():
    context = Folder()
    services = Folder()
    users = Folder()
    groups = Folder()
    principals = Folder()
    principals['groups'] = groups
    principals['users'] = users
    services['principals'] = principals
    services['objectmap'] = ObjectMap()
    context.add('__services__', services, allow_services=True)
    return context

