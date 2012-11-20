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
    def _callFUT(self, request):
        from ..helpers import breadcrumbs
        return breadcrumbs(request)

    def test_it(self):
        request = testing.DummyRequest()
        request.sdiapi = DummySDIAPI()
        result = self._callFUT(request)
        self.assertEqual(result, [])
    
class Test_get_sdi_title(unittest.TestCase):
    def _callFUT(self, request):
        from ..helpers import get_sdi_title
        return get_sdi_title(request)

    def test_it(self):
        request = testing.DummyRequest()
        request.sdiapi = DummySDIAPI()
        result = self._callFUT(request)
        self.assertEqual(result, 'abc')
        
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
    
class DummySDIAPI(object):
    def mgmt_path(self, *arg, **kw):
        return '/mgmt_path'

    def breadcrumbs(self):
        return []

    def sdi_title(self):
        return 'abc'
