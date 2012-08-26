import unittest
from pyramid import testing

class TestRoot(unittest.TestCase):
    def _makeOne(self):
        from . import Root
        return Root()

    def test_ctor(self):
        inst = self._makeOne()
        self.assertEqual(list(inst.items()), [])

    def _makeRegistry(self, settings):
        created = testing.DummyResource()
        group = testing.DummyResource()
        services = testing.DummyResource()
        services.add = services.__setitem__
        def connect(other):
            group.connected = other
        memberids = testing.DummyResource()
        memberids.connect = connect
        group.memberids = memberids
        group.__objectid__ = 1
        user = testing.DummyResource()
        def add_user(*arg, **kw):
            return user
        def add_group(*arg, **kw):
            return group
        created.add_user = add_user
        created.add_group = add_group
        def add(*arg, **kw):
            created.added = True
        created.add = add
        registry = testing.DummyResource()
        registry.settings = settings
        registry.content = testing.DummyResource()
        def create(type, *arg, **kw):
            if type == 'Services':
                return services
            return created
        registry.content.create = create
        registry.group = group
        registry.user = user
        registry.created = created
        return registry

    def test_after_create_with_password(self):
        settings = {
            'substanced.initial_password':'pass',
            'substanced.initial_login':'login',
            'substanced.initial_email':'email@example.com',
            }
        registry = self._makeRegistry(settings)
        inst = self._makeOne()
        inst.after_create(inst, registry)
        services = inst['__services__']
        self.assertTrue('objectmap' in services)
        self.assertTrue('principals' in services)
        self.assertTrue(registry.created.added)
        self.assertTrue(registry.group.connected)
        self.assertTrue(inst.__acl__)
        self.assertFalse(registry.created.__sd_deletable__)

    def test_after_create_without_password(self):
        from pyramid.exceptions import ConfigurationError
        settings = {}
        registry = self._makeRegistry(settings)
        inst = self._makeOne()
        self.assertRaises(ConfigurationError, inst.after_create, inst, registry)
