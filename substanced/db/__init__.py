import transaction
from pyramid_zodbconn import (
    get_connection,
    ZODBConnectionOpened,
    ZODBConnectionWillClose,
    )
from substanced.evolution import mark_unfinished_as_finished

from ..stats import statsd_incr
from ..event import RootAdded

def root_factory(request, t=transaction, g=get_connection,
                 mark_unfinished_as_finished=mark_unfinished_as_finished):
    """ A function which can be used as a Pyramid ``root_factory``.  It accepts
    a request and returns an instance of the ``Root`` content type."""
    # accepts "t", "g", and "mark_unfinished_as_finished" for unit testing
    # purposes only
    conn = g(request)
    zodb_root = conn.root()
    if not 'app_root' in zodb_root:
        registry = request.registry
        app_root = registry.content.create('Root')
        zodb_root['app_root'] = app_root
        t.savepoint() # give app_root a _p_jar
        registry.notify(RootAdded(app_root))
        mark_unfinished_as_finished(app_root, registry, t)
        t.commit()
    statsd_incr('root_factory', rate=.1)
    return zodb_root['app_root']

def connection_opened(event):
    request = event.request
    request._zodb_tx_counts = event.conn.getTransferCounts()

def connection_will_close(event, statsd_incr=statsd_incr):
    # statsd_incr is passed in above only for testing purposes
    request = event.request
    counts = getattr(request, '_zodb_tx_counts',  None)
    if counts is not None:
        loads_before, stores_before = counts
        loads_after, stores_after = event.conn.getTransferCounts()
        loads = loads_after - loads_before
        stores = stores_after - stores_before
        if loads:
            statsd_incr('zodb.loads', loads, registry=request.registry)
        if stores:
            statsd_incr('zodb.stores', stores, registry=request.registry)

def includeme(config):
    config.add_subscriber(connection_opened, ZODBConnectionOpened)
    config.add_subscriber(connection_will_close, ZODBConnectionWillClose)
