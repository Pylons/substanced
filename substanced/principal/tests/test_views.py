import unittest
import colander
from pyramid import testing

class TestAddUserView(unittest.TestCase):
    def _makeOne(self, context, request):
        from ..views import AddUserView
        return AddUserView(context, request)

    def _makeRequest(self, resource):
        request = testing.DummyRequest()
        request.registry = testing.DummyResource()
        request.registry.content = DummyContent(resource)
        request.mgmt_path = lambda *arg: 'http://example.com'
        return request

    def test_add_success(self):
        resource = DummyPrincipal()
        request = self._makeRequest(resource)
        context = testing.DummyResource()
        inst = self._makeOne(context, request)
        resp = inst.add_success({'login':'name', 'groups':(1,)})
        self.assertEqual(context['name'], resource)
        self.assertEqual(resp.location, 'http://example.com')
        self.assertEqual(resource.connected, (1,))

class TestAddGroupView(unittest.TestCase):
    def _makeOne(self, context, request):
        from ..views import AddGroupView
        return AddGroupView(context, request)

    def _makeRequest(self, resource):
        request = testing.DummyRequest()
        request.registry = testing.DummyResource()
        request.registry.content = DummyContent(resource)
        request.mgmt_path = lambda *arg: 'http://example.com'
        return request

    def test_add_success(self):
        resource = DummyPrincipal()
        request = self._makeRequest(resource)
        context = testing.DummyResource()
        inst = self._makeOne(context, request)
        resp = inst.add_success({'name':'name', 'members':(1,)})
        self.assertEqual(context['name'], resource)
        self.assertEqual(resp.location, 'http://example.com')

class Test_password_validator(unittest.TestCase):
    def _makeOne(self, node, kw):
        from ..views import password_validator
        return password_validator(node, kw)

    def test_it_success(self):
        request = testing.DummyRequest()
        context = testing.DummyResource()
        def check_password(pwd):
            return True
        context.check_password = check_password
        kw = dict(request=request, context=context)
        inst = self._makeOne(None, kw)
        self.assertEqual(inst(None, 'pwd'), None)

    def test_it_failure(self):
        request = testing.DummyRequest()
        context = testing.DummyResource()
        def check_password(pwd):
            return False
        context.check_password = check_password
        kw = dict(request=request, context=context)
        inst = self._makeOne(None, kw)
        self.assertRaises(colander.Invalid, inst, None, 'pwd')

class TestChangePasswordView(unittest.TestCase):
    def _makeOne(self, context, request):
        from ..views import ChangePasswordView
        return ChangePasswordView(context, request)

    def test_add_success(self):
        context = DummyPrincipal()
        request = testing.DummyRequest()
        request.mgmt_path = lambda *arg: 'http://example.com'
        inst = self._makeOne(context, request)
        resp = inst.change_success({'password':'password'})
        self.assertEqual(context.password, 'password')
        self.assertEqual(resp.location, 'http://example.com')
        self.assertTrue(request.session['_f_success'])

class TestRequestResetView(unittest.TestCase):
    def _makeOne(self, context, request):
        from ..views import ResetRequestView
        return ResetRequestView(context, request)

    def _makeRequest(self):
        request = testing.DummyRequest()
        request.mgmt_path = lambda *arg : 'http://example.com'
        return request

    def _makeSite(self):
        from ...testing import make_site
        return make_site()

    def test_send_success(self):
        site = self._makeSite()
        user = DummyPrincipal()
        site['__services__']['principals']['users']['user'] = user
        request = self._makeRequest()
        inst = self._makeOne(site, request)
        resp = inst.send_success({'login':'user'})
        self.assertEqual(resp.location, 'http://example.com')
        self.assertTrue(user.emailed_password_reset)

class TestResetView(unittest.TestCase):
    def _makeOne(self, context, request):
        from ..views import ResetView
        return ResetView(context, request)

    def _makeRequest(self):
        request = testing.DummyRequest()
        request.mgmt_path = lambda *arg : 'http://example.com'
        return request

    def test_reset_success(self):
        context = testing.DummyResource()
        def reset_password(password):
            self.assertEqual(password, 'thepassword')
        context.reset_password = reset_password
        request = self._makeRequest()
        inst = self._makeOne(context, request)
        resp = inst.reset_success({'new_password':'thepassword'})
        self.assertEqual(resp.location, 'http://example.com')
    

class Test_login_validator(unittest.TestCase):
    def _makeOne(self, node, kw):
        from ..views import login_validator
        return login_validator(node, kw)

    def _makeSite(self):
        from ...interfaces import IFolder
        site = testing.DummyResource(__provides__=IFolder)
        services = testing.DummyResource()
        principals = testing.DummyResource()
        users = testing.DummyResource()
        site['__services__'] = services
        services['principals'] = principals
        principals['users'] = users
        return site

    def test_no_such_user(self):
        import colander
        request = testing.DummyRequest()
        site = self._makeSite()
        inst = self._makeOne(None, dict(request=request, context=site))
        self.assertRaises(colander.Invalid, inst, None, 'fred')

    def test_user_exists(self):
        request = testing.DummyRequest()
        site = self._makeSite()
        fred = testing.DummyResource()
        site['__services__']['principals']['users']['fred'] = fred
        inst = self._makeOne(None, dict(request=request, context=site))
        self.assertEqual(inst(None, 'fred'), None)

class DummyPrincipal(object):
    def connect(self, *args):
        self.connected = args

    def set_password(self, password):
        self.password = password

    def email_password_reset(self, request):
        self.emailed_password_reset = True

class DummyContent(object):
    def __init__(self, resource):
        self.resource = resource

    def create(self, iface, *arg, **kw):
        return self.resource
        
        
