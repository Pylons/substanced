import unittest
from pyramid import testing

class Test_macros(unittest.TestCase):
    def setUp(self):
        testing.setUp()

    def tearDown(self):
        testing.tearDown()
        
    def _callFUT(self):
        from ..helpers import macros
        return macros()

    def test_it(self):
        val = self._callFUT()
        self.assertTrue('master' in val)

class Test_breadcrumbs(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
    
    def _callFUT(self, request):
        from ..helpers import breadcrumbs
        return breadcrumbs(request)
    
    def test_no_permissions(self):
        self.config.testing_securitypolicy(permissive=False)
        resource = testing.DummyResource()
        request = testing.DummyRequest()
        request.context = resource
        result = self._callFUT(request)
        self.assertEqual(result, [])
        
    def test_with_permissions(self):
        self.config.testing_securitypolicy(permissive=True)
        resource = testing.DummyResource()
        request = testing.DummyRequest()
        request.mgmt_path = lambda *arg: '/path'
        request.context = resource
        request.registry.content = DummyContent()
        result = self._callFUT(request)
        self.assertEqual(
            result,
             [{'url': '/path',
               'active': 'active',
               'name': 'Home',
               'icon': None}]
            )

class Test_get_site_title(unittest.TestCase):
    def _callFUT(self, request):
        from ..helpers import get_site_title
        return get_site_title(request)
        
    def test_it(self):
        from ...interfaces import ISite
        resource = testing.DummyResource(__provides__=ISite)
        resource.title = 'My Title'
        request = testing.DummyRequest()
        request.context = resource
        result = self._callFUT(request)
        self.assertEqual(result, 'My Title')

class Test_add_renderer_globals(unittest.TestCase):
    def _callFUT(self, event):
        from ..helpers import add_renderer_globals
        add_renderer_globals(event)

    def test_it(self):
        from .. import helpers
        e = {}
        self._callFUT(e)
        self.assertEqual(e['sdi_h'], helpers)
        
class DummyContent(object):
    def metadata(self, context, name, default=None):
        return default
    
