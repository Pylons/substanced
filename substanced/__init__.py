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

def include(config): # pragma: no cover
    config.include('pyramid_zodbconn')
    config.include('pyramid_mailer')
    config.include('.event')
    config.include('.sdi')
    config.include('.content')
    config.include('.objectmap')
    config.include('.property')
    config.include('.catalog')
    config.include('.evolution')
    config.include('.widget')
    config.include('.workflow')

def scan(config): # pragma: no cover
    config.scan('.catalog')
    config.scan('.file')
    config.scan('.folder')
    config.scan('.objectmap')
    config.scan('.principal')
    config.scan('.root')
    config.scan('.sdi')
    
def includeme(config): # pragma: no cover
    # NB: includes of packages which register directives must be done before
    # scans of packages which use venusian decorators that use those directives
    # e.g. (@subscribe_*, @mgmt_view, @content).  This is why we do all
    # includes first, then we scan afterwards instead of intermingling scans
    # and includes.
    config.include(include)
    config.include(scan)
