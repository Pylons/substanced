import unittest
from pyramid import testing

class Test_root_factory(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
        
    def _callFUT(self, request, transaction, get_connection):
        from . import root_factory
        return root_factory(request, transaction, get_connection)

    def _makeRequest(self, settings):
        request = Dummy()
        request.registry = Dummy()
        def notify(event):
            request.registry.event = event
        request.registry.notify = notify
        request.registry.settings = settings
        return request

    def test_without_app_root_with_initial_password(self):
        txn = DummyTransaction()
        root = {}
        gc = Dummy_get_connection(root)
        settings = {
            'substanced.initial_password':'pass',
            'substanced.initial_login':'login',
            'substanced.initial_email':'email@example.com',
            }
        request = self._makeRequest(settings)
        root = testing.DummyResource()
        root['__services__'] = testing.DummyResource()
        root.add_service = root['__services__'].__setitem__
        objectmap = testing.DummyResource()
        def objectmap_add(root, tuple):
            objectmap.added = root, tuple
        objectmap.add = objectmap_add
        principals = testing.DummyResource()
        user = testing.DummyResource()
        group = testing.DummyResource()
        def connect(user):
            group.user = user
        group.connect = connect
        group.__objectid__ = 1
        principals['users'] = testing.DummyResource()
        principals['users'].add_user = lambda *arg: user
        principals['groups'] = testing.DummyResource()
        principals['groups'].add_group = lambda *arg: group
        objects = [
            ('Root', root),
            ('Object Map', objectmap),
            ('Principals', principals),
            ]
        class DummyContent(object):
            def create(innerself, name, *arg, **kw):
                next_name, next_ob = objects.pop(0)
                self.assertEqual(name, next_name)
                return next_ob
        request.registry.content = DummyContent()
        result = self._callFUT(request, txn, gc)
        self.assertEqual(root['__services__']['principals'], principals)
        self.assertEqual(root['__services__']['objectmap'], objectmap)
        self.assertEqual(group.user, user)
        self.assertEqual(objectmap.added, (root, ('',)))
        self.assertEqual(result, root)
        self.assertTrue(txn.committed)

    def test_without_app_root_no_initial_password(self):
        from pyramid.exceptions import ConfigurationError
        txn = DummyTransaction()
        root = {}
        gc = Dummy_get_connection(root)
        settings = {}
        request = self._makeRequest(settings)
        root = Dummy()
        self.assertRaises(ConfigurationError, self._callFUT, request, txn, gc)
        self.assertFalse(txn.committed)

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

class Dummy(object):
    pass

