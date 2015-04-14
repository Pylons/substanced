import unittest
from pyramid import testing

class TestIndexViewDiscriminator(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
        
    def _makeOne(self, catalog_name, index_name):
        from ..discriminators import IndexViewDiscriminator
        return IndexViewDiscriminator(catalog_name, index_name)

    def test_ctor(self):
        inst = self._makeOne('system', 'attr')
        self.assertEqual(inst.catalog_name, 'system')
        self.assertEqual(inst.index_name, 'attr')

    def test_call_no_index_view(self):
        inst = self._makeOne('system', 'attr')
        result = inst(None, True)
        self.assertEqual(result, True)

    def test_call_with_index_view(self):
        from zope.interface import Interface
        from substanced.interfaces import IIndexView
        registry = self.config.registry
        resource = testing.DummyResource()
        def view(_resource, default):
            self.assertEqual(default, True)
            self.assertEqual(_resource, resource)
            return True
        registry.registerAdapter(view, (Interface,), IIndexView, 'system|attr')
        inst = self._makeOne('system', 'attr')
        result = inst(resource, True)
        self.assertEqual(result, True)
        
            

class Test_dummy_discriminator(unittest.TestCase):
    def _callFUT(self, object, default):
        from ..discriminators import dummy_discriminator
        return dummy_discriminator(object, default)

    def test_it(self):
        result = self._callFUT(None, '123')
        self.assertEqual(result, '123')

