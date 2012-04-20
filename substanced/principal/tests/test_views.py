import unittest
import colander
from pyramid import testing

class TestAddUserView(unittest.TestCase):
    def _makeOne(self, request):
        from ..views import AddUserView
        return AddUserView(request)

    def _makeRequest(self, resource):
        request = testing.DummyRequest()
        request.registry.content = DummyContent(resource)
        request.mgmt_path = lambda *arg: 'http://example.com'
        request.context = testing.DummyResource()
        return request

    def test_add_success(self):
        resource = DummyPrincipal()
        request = self._makeRequest(resource)
        inst = self._makeOne(request)
        resp = inst.add_success({'login':'name', 'groups':(1,)})
        self.assertEqual(request.context['name'], resource)
        self.assertEqual(resp.location, 'http://example.com')
        self.assertEqual(resource.connected, (1,))

class TestAddGroupView(unittest.TestCase):
    def _makeOne(self, request):
        from ..views import AddGroupView
        return AddGroupView(request)

    def _makeRequest(self, resource):
        request = testing.DummyRequest()
        request.registry.content = DummyContent(resource)
        request.mgmt_path = lambda *arg: 'http://example.com'
        request.context = testing.DummyResource()
        return request

    def test_add_success(self):
        resource = DummyPrincipal()
        request = self._makeRequest(resource)
        inst = self._makeOne(request)
        resp = inst.add_success({'name':'name', 'members':(1,)})
        self.assertEqual(request.context['name'], resource)
        self.assertEqual(resp.location, 'http://example.com')

class Test_password_validator(unittest.TestCase):
    def _makeOne(self, node, kw):
        from ..views import password_validator
        return password_validator(node, kw)

    def test_it_success(self):
        request = testing.DummyRequest()
        context = testing.DummyResource()
        request.context = context
        def check_password(pwd):
            return True
        context.check_password = check_password
        kw = dict(request=request)
        inst = self._makeOne(None, kw)
        self.assertEqual(inst(None, 'pwd'), None)

    def test_it_failure(self):
        request = testing.DummyRequest()
        context = testing.DummyResource()
        request.context = context
        def check_password(pwd):
            return False
        context.check_password = check_password
        kw = dict(request=request)
        inst = self._makeOne(None, kw)
        self.assertRaises(colander.Invalid, inst, None, 'pwd')
        
class DummyPrincipal(object):
    def connect(self, *args):
        self.connected = args

class DummyContent(object):
    def __init__(self, resource):
        self.resource = resource

    def create(self, iface, *arg, **kw):
        return self.resource
        
        
