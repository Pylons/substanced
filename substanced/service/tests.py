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

class Test_find_services(unittest.TestCase):
    def _callFUT(self, context, name):
        from . import find_services
        return find_services(context, name)
    
    def test_one_found(self):
        from ..interfaces import IFolder
        site = testing.DummyResource(__provides__=IFolder)
        services = testing.DummyResource()
        catalog = testing.DummyResource()
        services['catalog'] = catalog
        site['__services__'] = services
        self.assertEqual(self._callFUT(site, 'catalog'), [catalog])
        
    def test_two_found(self):
        from ..interfaces import IFolder
        folder = testing.DummyResource(__provides__=IFolder)
        services1 = testing.DummyResource()
        catalog1 = testing.DummyResource()
        services1['catalog'] = catalog1
        folder['__services__'] = services1
        site = testing.DummyResource(__provides__=IFolder)
        services2 = testing.DummyResource()
        catalog2 = testing.DummyResource()
        services2['catalog'] = catalog2
        site['__services__'] = services2
        site['folder'] = folder
        self.assertEqual(self._callFUT(folder, 'catalog'), [catalog1, catalog2])
    
    def test_unfound(self):
        from ..interfaces import IFolder
        site = testing.DummyResource(__provides__=IFolder)
        services = testing.DummyResource()
        site['__services__'] = services
        self.assertEqual(self._callFUT(site, 'catalog'), [])
