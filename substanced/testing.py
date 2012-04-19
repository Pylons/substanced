from pyramid import testing

def make_site():
    from .interfaces import IFolder
    context = testing.DummyResource(__provides__=IFolder)
    services = testing.DummyResource()
    users = testing.DummyResource()
    groups = testing.DummyResource()
    principals = testing.DummyResource()
    principals['groups'] = groups
    principals['users'] = users
    services['principals'] = principals
    context['__services__'] = services
    services['principals'] = principals
    context['__services__'] = services
    return context

