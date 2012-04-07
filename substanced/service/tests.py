import unittest
from pyramid import testing

class Test_find_service(unittest.TestCase):
    def _callFUT(self, context, name):
        from . import find_service
        return find_service(context, name)
    
    def test_unfound(self):
        from ..interfaces import IFolder
        site = testing.DummyResource(__provides__=IFolder)
        services = testing.DummyResource()
        site['__services__'] = services
        self.assertEqual(self._callFUT(site, 'catalog'), None)
        
    def test_found(self):
        from ..interfaces import IFolder
        site = testing.DummyResource(__provides__=IFolder)
        services = testing.DummyResource()
        catalog = testing.DummyResource
        services['catalog'] = catalog
        site['__services__'] = services
        self.assertEqual(self._callFUT(site, 'catalog'), catalog)
