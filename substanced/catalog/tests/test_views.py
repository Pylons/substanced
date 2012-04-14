import unittest
from pyramid import testing

class TestManageCatalog(unittest.TestCase):
    def _makeOne(self, context, request):
        from ..views import ManageCatalog
        return ManageCatalog(context, request)

    def test_GET(self):
        context = DummyCatalog()
        request = testing.DummyRequest()
        inst = self._makeOne(context, request)
        result = inst.GET()
        self.assertEqual(result['cataloglen'], 0)

    def test_POST(self):
        from .. import logger
        context = DummyCatalog()
        request = testing.DummyRequest()
        request.mgmt_path = lambda *arg: '/manage'
        request.params['csrf_token'] = request.session.get_csrf_token()
        inst = self._makeOne(context, request)
        result = inst.POST()
        self.assertEqual(result.location, '/manage')
        self.assertEqual(context.output, logger.info)

class DummyCatalog(object):
    def __init__(self):
        self.objectids = ()

    def reindex(self, output=None):
        self.output = output
        
