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

class Test_login(unittest.TestCase):
    def setUp(self):
        testing.setUp()

    def tearDown(self):
        testing.tearDown()
        
    def _callFUT(self, context, request):
        from ..views import login
        return login(context, request)

    def test_form_not_submitted(self):
        request = testing.DummyRequest()
        request.mgmt_path = lambda *arg: '/path'
        context = testing.DummyResource()
        result = self._callFUT(context, request)
        self.assertEqual(result['url'], '/path')
        self.assertEqual(result['came_from'], 'http://example.com')
        self.assertEqual(result['login'], '')
        self.assertEqual(result['password'], '')

    def test_form_submitted_csrf_error(self):
        request = testing.DummyRequest()
        request.params['form.submitted'] = True
        request.mgmt_path = lambda *arg: '/path'
        context = testing.DummyResource()
        result = self._callFUT(context, request)
        self.assertEqual(result['url'], '/path')
        self.assertEqual(result['came_from'], 'http://example.com')
        self.assertEqual(result['login'], '')
        self.assertEqual(result['password'], '')
        self.assertEqual(request.session['_f_error'], ['Failed login (CSRF)'])
        
    def test_form_submitted_failed_login_no_user(self):
        from ...testing import make_site
        request = testing.DummyRequest()
        request.params['form.submitted'] = True
        request.params['login'] = 'login'
        request.params['password'] = 'password'
        request.mgmt_path = lambda *arg: '/path'
        request.params['csrf_token'] = request.session.get_csrf_token()
        context = make_site()
        result = self._callFUT(context, request)
        self.assertEqual(result['url'], '/path')
        self.assertEqual(result['came_from'], 'http://example.com')
        self.assertEqual(result['login'], 'login')
        self.assertEqual(result['password'], 'password')
        self.assertEqual(request.session['_f_error'], ['Failed login'])

    def test_form_submitted_failed_login_wrong_password(self):
        from ...testing import make_site
        request = testing.DummyRequest()
        request.params['form.submitted'] = True
        request.params['login'] = 'login'
        request.params['password'] = 'password'
        request.mgmt_path = lambda *arg: '/path'
        request.params['csrf_token'] = request.session.get_csrf_token()
        context = make_site()
        context['principals']['users']['login'] = DummyUser(0)
        context.__services__ = ('principals',)
        result = self._callFUT(context, request)
        self.assertEqual(result['url'], '/path')
        self.assertEqual(result['came_from'], 'http://example.com')
        self.assertEqual(result['login'], 'login')
        self.assertEqual(result['password'], 'password')
        self.assertEqual(request.session['_f_error'], ['Failed login'])

    def test_form_submitted_success(self):
        from ...testing import make_site
        request = testing.DummyRequest()
        request.params['form.submitted'] = True
        request.params['login'] = 'login'
        request.params['password'] = 'password'
        request.mgmt_path = lambda *arg: '/path'
        request.params['csrf_token'] = request.session.get_csrf_token()
        context = make_site()
        user = DummyUser(1)
        user.__objectid__ = 1
        context['principals']['users']['login'] = user
        context.__services__ = ('principals',)
        result = self._callFUT(context, request)
        self.assertEqual(result.location, 'http://example.com')
        self.assertTrue(result.headers)
        self.assertEqual(request.session['_f_success'], ['Welcome!'])

class TestManagementViews(unittest.TestCase):
    def _makeOne(self, context, request):
        from ..views import ManagementViews
        return ManagementViews(context, request)

    def test_manage_main_no_view_data(self):
        context = testing.DummyResource()
        request = testing.DummyRequest()
        def mgmt_path(ctx, value):
            self.assertEqual(value, '@@login')
            return '/path'
        request.mgmt_path = mgmt_path
        inst = self._makeOne(context, request)
        inst.sdi_mgmt_views = lambda *arg: []
        result = inst.manage_main()
        self.assertEqual(request.session['came_from'], 'http://example.com')
        self.assertEqual(result.location, '/path')

    def test_manage_main_with_view_data(self):
        context = testing.DummyResource()
        request = testing.DummyRequest()
        def mgmt_path(ctx, value):
            self.assertEqual(value, '@@fred')
            return '/path'
        request.mgmt_path = mgmt_path
        inst = self._makeOne(context, request)
        inst.sdi_mgmt_views = lambda *arg: [{'view_name':'fred'}]
        result = inst.manage_main()
        self.assertEqual(result.location, '/path')

    def test_add_content_no_views(self):
        context = testing.DummyResource()
        request = testing.DummyRequest()
        inst = self._makeOne(context, request)
        inst.sdi_add_views = lambda *arg: []
        result = inst.add_content()
        self.assertEqual(result, {'views':[]})
        
    def test_add_content_with_one_view(self):
        context = testing.DummyResource()
        request = testing.DummyRequest()
        inst = self._makeOne(context, request)
        inst.sdi_add_views = lambda *arg: [{'url':'http://foo'}]
        result = inst.add_content()
        self.assertEqual(result.location, 'http://foo')

class TestManageDatabase(unittest.TestCase):
    def _makeOne(self, context, request):
        from ..views import ManageDatabase
        return ManageDatabase(context, request)

    def test_view_with_activity_monitor(self):
        context = testing.DummyResource()
        request = testing.DummyRequest()
        inst = self._makeOne(context, request)
        am = DummyActivityMonitor()
        conn = DummyConnection(am=am)
        inst.get_connection = lambda *arg: conn
        result = inst.view()
        self.assertEqual(result['data_connections'], '[[1000, 1], [1000, 1]]')
        self.assertEqual(result['data_object_loads'], '[[1000, 1], [1000, 1]]')
        self.assertEqual(result['data_object_stores'], '[[1000, 1], [1000, 1]]')

    def test_view_no_activity_monitor(self):
        context = testing.DummyResource()
        request = testing.DummyRequest()
        inst = self._makeOne(context, request)
        conn = DummyConnection(am=None)
        inst.get_connection = lambda *arg: conn
        result = inst.view()
        self.assertEqual(result['data_connections'], '[]')
        self.assertEqual(result['data_object_loads'], '[]')
        self.assertEqual(result['data_object_stores'], '[]')

    def test_pack(self):
        context = testing.DummyResource()
        request = testing.DummyRequest()
        inst = self._makeOne(context, request)
        conn = DummyConnection(am=None)
        inst.get_connection = lambda *arg: conn
        request.POST['days'] = '5'
        request.mgmt_path = lambda *arg: '/'
        resp = inst.pack()
        self.assertEqual(conn._db.packed, 5)
        self.assertEqual(resp.location, '/')

    def test_pack_invalid_days(self):
        from pyramid.httpexceptions import HTTPFound
        context = testing.DummyResource()
        request = testing.DummyRequest()
        inst = self._makeOne(context, request)
        conn = DummyConnection(am=None)
        inst.get_connection = lambda *arg: conn
        request.POST['days'] = 'p'
        request.mgmt_path = lambda *arg: '/'
        self.assertRaises(HTTPFound, inst.pack)

    def test_flush_cache(self):
        context = testing.DummyResource()
        request = testing.DummyRequest()
        inst = self._makeOne(context, request)
        conn = DummyConnection(am=None)
        inst.get_connection = lambda *arg: conn
        request.POST['days'] = '5'
        request.mgmt_path = lambda *arg: '/'
        resp = inst.flush_cache()
        self.assertTrue(conn._db.minimized)
        self.assertEqual(resp.location, '/')

class DummyDB(object):
    def __init__(self, am=None):
        self.am = am

    def getActivityMonitor(self):
        return self.am

    def pack(self, days=None):
        self.packed = days

    def cacheMinimize(self):
        self.minimized = True

class DummyActivityMonitor(object):
    def getActivityAnalysis(self):
        return [{'end':1, 'connections':1, 'stores':1, 'loads':1}]*2

class DummyConnection(object):
    def __init__(self, am=None):
        self._db = DummyDB(am=am)

    def db(self):
        return self._db

class DummyUser(object):
    def __init__(self, result):
        self.result = result

    def check_password(self, password):
        return self.result
