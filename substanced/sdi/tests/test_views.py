import unittest
from pyramid import testing

class Test_logout(unittest.TestCase):
    def setUp(self):
        testing.setUp()

    def tearDown(self):
        testing.tearDown()
        
    def _callFUT(self, request):
        from ..views import logout
        return logout(request)

    def test_it(self):
        request = testing.DummyRequest()
        request.mgmt_path = lambda *arg: '/path'
        response = self._callFUT(request)
        self.assertEqual(response.location, '/path')
