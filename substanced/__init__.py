import transaction
from pyramid_zodbconn import get_connection

def root_factory(request, t=transaction, g=get_connection):
    """ A function which can be used as a Pyramid ``root_factory``.  It
    accepts a request and returns an instance of the ``Root`` content type."""
    # accepts "t" and "g" for unit testing purposes only
    conn = g(request)
    zodb_root = conn.root()
    if not 'app_root' in zodb_root:
        registry = request.registry
        app_root = registry.content.create('Root')
        zodb_root['app_root'] = app_root
        t.commit()
    return zodb_root['app_root']

def includeme(config): # pragma: no cover
    config.include('pyramid_zodbconn')
    config.include('pyramid_mailer')
    # include('.event') must be done before scans of packages which use
    # @subscribe_* decorators
    config.include('.event') 
    # include('.sdi') must be done before scans of packages which use
    # @mgmt_view decorators
    config.include('.sdi')
    # include('.content') must be done before scans of packages which use
    # @content decorators
    config.include('.content')
    config.include('.objectmap')
    config.include('.property')
    config.include('.catalog')
    config.include('.root')
    config.include('.evolution')
    config.include('.folder')
    config.include('.principal')
    config.include('.widget')
    config.include('.file')
    config.include('.workflow')
