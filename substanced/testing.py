from .objectmap import ObjectMap
from .folder import Folder

def make_site():
    context = Folder()
    ObjectMap(context)
    users = Folder()
    groups = Folder()
    principals = Folder()
    principals['groups'] = groups
    principals['users'] = users
    context.add_service('principals', principals)
    return context

