import unittest
from pyramid import testing
from pyramid.exceptions import ConfigurationError

class Test_root_factory(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
        
    def _callFUT(self, request, transaction, get_connection):
        from . import Site
        return Site.root_factory(request, transaction, get_connection)

    def test_without_app_root_no_initial_password(self):
        txn = DummyTransaction()
        root = {}
        gc = Dummy_get_connection(root)
        request = testing.DummyRequest()
        self.assertRaises(ConfigurationError, self._callFUT, request, txn, gc)

    def test_without_app_root_with_initial_password(self):
        from ..objectmap import object_will_be_added
        from zope.interface import Interface
        from substanced.event import IObjectWillBeAdded
        self.config.add_subscriber(
            object_will_be_added, [Interface,IObjectWillBeAdded])
        # ^^^ to get user.__objectid__ set up right
        txn = DummyTransaction()
        root = {}
        gc = Dummy_get_connection(root)
        request = testing.DummyRequest()
        request.registry.settings['substanced.initial_password'] = 'admin'
        result = self._callFUT(request, txn, gc)
        self.assertEqual(result.__class__.__name__, 'Site')
        self.assertTrue(txn.committed)

    def test_with_app_root(self):
        txn = DummyTransaction()
        app_root = object()
        root = {'app_root':app_root}
        gc = Dummy_get_connection(root)
        request = testing.DummyRequest()
        result = self._callFUT(request, txn, gc)
        self.assertEqual(result, app_root)
        self.assertFalse(txn.committed)
        
class DummyTransaction(object):
    committed = False
    def commit(self):
        self.committed = True

class Dummy_get_connection(object):
    def __init__(self, root):
        self._root = root

    def root(self):
        return self._root

    def __call__(self, request):
        return self
