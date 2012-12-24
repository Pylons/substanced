import contextlib
import statsd

from pyramid.threadlocal import get_current_registry
from pyramid.settings import asbool

from ..interfaces import IStatsDConnection

@contextlib.contextmanager
def statsd_timer(timer_name, registry=None):
    if registry is None:
        registry = get_current_registry()
    connection = registry.queryUtility(IStatsDConnection)
    if connection is None:
        yield
    else:
        statsd_timer = statsd.Timer('substanced', connection=connection)
        statsd_timer.start()
        try:
            yield
        finally:
            statsd_timer.stop(timer_name)
    
def includeme(config):
    settings = config.registry.settings
    statsd_enabled = asbool(settings.get('substanced.statsd.enabled', False))
    if statsd_enabled:
        host = settings.get('substanced.statsd.host', 'localhost')
        port = int(settings.get('substanced.statsd.port', 8125))
        rate = int(settings.get('substanced.statsd.sample_rate', 1))
        connection = statsd.Connection(host=host, port=port, sample_rate=rate)
        config.registry.registerUtility(connection, IStatsDConnection)
