import transaction
from pyramid_zodbconn import get_connection
from substanced.evolution import evolve_packages

from .stats import statsd_incr

def root_factory(request, t=transaction, g=get_connection,
                 evolve_packages=evolve_packages):
    """ A function which can be used as a Pyramid ``root_factory``.  It
    accepts a request and returns an instance of the ``Root`` content type."""
    # accepts "t", "g", and "evolve_packages" for unit testing purposes only
    conn = g(request)
    zodb_root = conn.root()
    if not 'app_root' in zodb_root:
        registry = request.registry
        app_root = registry.content.create('Root')
        zodb_root['app_root'] = app_root
        t.savepoint() # give app_root a _p_jar
        evolve_packages(
            registry,
            app_root,
            mark_all_current=True,
            )
        t.commit()
    statsd_incr('root_factory', rate=.1)
    return zodb_root['app_root']

def include(config): # pragma: no cover
    """ Perform all ``config.include`` tasks required for Substance D and the
    default aspects of the SDI to work."""
    config.include('pyramid_zodbconn')
    config.include('pyramid_mailer')
    config.include('.stats')
    config.include('.folder')
    config.include('.event')
    config.include('.sdi')
    config.include('.content')
    config.include('.objectmap')
    config.include('.property')
    config.include('.catalog')
    config.include('.evolution')
    config.include('.widget')
    config.include('.workflow')
    config.include('.dump')

def scan(config): # pragma: no cover
    """ Perform all ``config.scan`` tasks required for Substance D and the
    default aspects of the SDI to work."""
    config.scan('.stats')
    config.scan('.catalog')
    config.scan('.file')
    config.scan('.folder')
    config.scan('.objectmap')
    config.scan('.principal')
    config.scan('.root')
    config.scan('.sdi')
    config.scan('.workflow')
    
def includeme(config): # pragma: no cover
    """ Do the work of :func:`substanced.include`, then
    :func:`substanced.scan`.  Makes ``config.include(substanced)`` work."""
    # NB: includes of packages which register directives must be done before
    # scans of packages which use venusian decorators that use those directives
    # e.g. (@subscribe_*, @mgmt_view, @content).  This is why we do all
    # includes first, then we scan afterwards instead of intermingling scans
    # and includes.
    config.include(include)
    config.include(scan)
