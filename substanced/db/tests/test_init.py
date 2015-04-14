import unittest
from pyramid import testing

class Test_root_factory(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
        
    def _callFUT(self, request, transaction, get_connection, evolve_packages):
        from .. import root_factory
        return root_factory(request, transaction, get_connection,
                            evolve_packages)

    def _makeRequest(self, app_root=None):
        request = Dummy()
        request.registry = DummyRegistry()
        request.registry.content = Dummy()
        request.registry.content.create = lambda *arg: app_root
        return request

    def test_without_app_root(self):
        txn = DummyTransaction()
        root = {}
        gc = Dummy_get_connection(root)
        ep = DummyFunction(True)
        app_root = object()
        request = self._makeRequest(app_root)
        result = self._callFUT(request, txn, gc, ep)
        self.assertEqual(result, app_root)
        self.assertTrue(txn.committed)
        self.assertTrue(txn.savepointed)
        self.assertTrue(ep.called)
        
    def test_with_app_root(self):
        txn = DummyTransaction()
        app_root = object()
        root = {'app_root':app_root}
        gc = Dummy_get_connection(root)
        ep = DummyFunction(True)
        request = testing.DummyRequest()
        result = self._callFUT(request, txn, gc, ep)
        self.assertEqual(result, app_root)
        self.assertFalse(txn.committed)

class Test_includeme(unittest.TestCase):
    def test_it(self):
        from .. import (
            includeme,
            connection_opened,
            connection_will_close,
            ZODBConnectionOpened,
            ZODBConnectionWillClose,
            )
        config = DummyConfig()
        includeme(config)
        self.assertEqual(
            config.subscriptions,
            [(connection_opened, ZODBConnectionOpened),
             (connection_will_close, ZODBConnectionWillClose),
             ]
            )

class Test_connection_opened(unittest.TestCase):
    def test_it(self):
        from  .. import connection_opened
        event = DummyEvent()
        connection_opened(event)
        self.assertEqual(event.request._zodb_tx_counts, (0,0))

class Test_connection_will_close(unittest.TestCase):
    def _callFUT(self, event, statsd_incr):
        from  .. import connection_will_close
        return connection_will_close(event, statsd_incr)

    def test_no_tx_counts(self):
        event = DummyEvent()
        result = self._callFUT(event, None)
        self.assertEqual(result, None) # doesnt fail

    def test_with_postitive_tx_counts(self):
        event = DummyEvent(5,5)
        event.request._zodb_tx_counts = (1, 1)
        L = []
        def statsd_incr(name, num, registry=None):
            L.append((name, num))
        self._callFUT(event, statsd_incr)
        self.assertEqual(
            L,
            [('zodb.loads', 4), ('zodb.stores', 4)]
            )

    def test_with_zero_tx_counts(self):
        event = DummyEvent(1,1)
        event.request._zodb_tx_counts = (1, 1)
        L = []
        self._callFUT(event, None)
        self.assertEqual(
            L,
            []
            )

class DummyTransaction(object):
    committed = False
    savepointed = False
    def commit(self):
        self.committed = True

    def savepoint(self):
        self.savepointed = True

class Dummy_get_connection(object):
    def __init__(self, root):
        self._root = root

    def root(self):
        return self._root

    def __call__(self, request):
        return self

class DummyFunction(object):
    called = False
    def __init__(self, result):
        self.result = result
    def __call__(self, *args, **kw):
        self.called = True
        self.args = args
        self.kw = kw
        return self.result

class Dummy(object):
    pass

class DummyRegistry(object):
    def notify(self, event):
        self.event = event

class DummyConfig(object):
    def __init__(self):
        self.subscriptions = []
    def add_subscriber(self, fn, event_type):
        self.subscriptions.append((fn, event_type))

class DummyConnection(object):
    def __init__(self, loads, stores):
        self.loads = loads
        self.stores = stores

    def getTransferCounts(self):
        return (self.loads, self.stores)

class DummyEvent(object):
    def __init__(self, loads=0, stores=0):
        self.request = testing.DummyRequest()
        self.conn = DummyConnection(loads, stores)
