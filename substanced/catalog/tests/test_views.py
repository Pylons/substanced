import unittest
from pyramid import testing

class TestManageCatalog(unittest.TestCase):
    def _makeOne(self, context, request):
        from ..views import ManageCatalog
        return ManageCatalog(context, request)

    def test_view(self):
        context = DummyCatalog()
        request = testing.DummyRequest()
        request.mgmt_path = lambda *arg: '/manage'
        inst = self._makeOne(context, request)
        result = inst.view()
        self.assertEqual(result['cataloglen'], 0)

    def test_reindex(self):
        context = DummyCatalog()
        request = testing.DummyRequest()
        request.mgmt_path = lambda *arg: '/manage'
        inst = self._makeOne(context, request)
        result = inst.reindex()
        self.assertEqual(result.location, '/manage')
        self.assertEqual(context.reindexed, True)

    def test_refresh(self):
        context = DummyCatalog()
        request = testing.DummyRequest()
        request.mgmt_path = lambda *arg: '/manage'
        inst = self._makeOne(context, request)
        result = inst.refresh()
        self.assertEqual(result.location, '/manage')
        self.assertEqual(context.refreshed, True)
        
class DummyCatalog(object):
    def __init__(self):
        self.objectids = ()

    def reindex(self):
        self.reindexed = True

    def refresh(self, registry):
        self.refreshed = True
        
        
