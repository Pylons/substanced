import transaction
from pyramid_zodbconn import get_connection
from .event import RootCreated

def root_factory(request, t=transaction, g=get_connection):
    """ A function which can be used as a Pyramid ``root_factory``.  It
    accepts a request and returns an instance of the ``Root`` content type."""
    # accepts "t" and "g" for unit testing purposes only
    conn = g(request)
    zodb_root = conn.root()
    if not 'app_root' in zodb_root:
        settings = request.registry.settings
        app_root = request.registry.content.create('Root', settings)
        zodb_root['app_root'] = app_root
        created = RootCreated(app_root, request.registry)
        request.registry.notify(created)
        t.commit()
    return zodb_root['app_root']

def includeme(config): # pragma: no cover
    config.include('pyramid_zodbconn')
    config.include('pyramid_mailer')
    config.include('.sdi')
    config.include('.content')
    config.include('.acl')
    config.include('.objectmap')
    config.include('.catalog')
    config.include('.root')
    config.include('.site')
    config.include('.evolution')
    config.include('.folder')
    config.include('.principal')
    config.include('.undo')
    config.include('.property')
    config.include('.widget')
    config.include('.file')
    config.include('.workflow')
