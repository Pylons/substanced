import unittest

from pyramid import testing

class TestACLView(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _makeOne(self, context, request):
        from ..acl import ACLEditViews
        return ACLEditViews(context, request).acl_view

    def test_view(self):
        from ....testing import make_site
        request = testing.DummyRequest()
        site = make_site()
        site['page'] = context = testing.DummyResource()
        site.__acl__ = context.__acl__ = [(None, 1, (None,))]
        user = DummyUser(1, u'john')
        site['principals']['users']['john'] = user
        site.__objectmap__ = DummyObjectMap({1:user})
        inst = self._makeOne(context, request)
        resp = inst()
        self.assertEqual(resp['parent_acl'], [(None, u'john', (None,))])
        self.assertEqual(resp['users'], [(1, u'john')])
        self.assertEqual(resp['groups'], [('system.Everyone',
                                          'system.Everyone'),
                                          ('system.Authenticated',
                                          'system.Authenticated')])
        self.assertEqual(resp['local_acl'], [(None, u'john', (None,))])
        self.assertEqual(resp['permissions'], ['-- ALL --'])
        self.assertEqual(resp['inheriting'], 'enabled')

class TestMoveUp(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _makeOne(self, context, request):
        from ..acl import ACLEditViews
        return ACLEditViews(context, request).move_up

    def test_view(self):
        from ....testing import make_site
        request = testing.DummyRequest()
        request.sdiapi = DummySDIAPI()
        token = request.session.new_csrf_token()
        request.POST['csrf_token'] = token
        request.POST['index'] = 1
        site = make_site()
        site['page'] = context = testing.DummyResource()
        site.__acl__ = [(None, 1, (None,))]
        context.__acl__ = [(None, 1, (None,)),
                           (None, 2, (None,))]
        user = DummyUser(1, u'john')
        user2 = DummyUser(2, u'mary')
        site['principals']['users']['john'] = user
        site.__objectmap__ = DummyObjectMap({1:user, 2:user2})
        inst = self._makeOne(context, request)
        resp = inst()
        self.assertEqual(resp['parent_acl'], [(None, u'john', (None,))])
        self.assertEqual(resp['users'], [(1, u'john')])
        self.assertEqual(resp['groups'], [('system.Everyone',
                                          'system.Everyone'),
                                          ('system.Authenticated',
                                          'system.Authenticated')])
        self.assertEqual(resp['local_acl'], [(None, u'mary', (None,)),
                                             (None, u'john', (None,))])
        self.assertEqual(resp['permissions'], ['-- ALL --'])
        self.assertEqual(resp['inheriting'], 'enabled')
        self.assertEqual(request.sdiapi.flashed, 'ACE moved up')

class TestMoveDown(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _makeOne(self, context, request):
        from ..acl import ACLEditViews
        return ACLEditViews(context, request).move_down

    def test_view(self):
        from ....testing import make_site
        request = testing.DummyRequest()
        request.sdiapi = DummySDIAPI()
        token = request.session.new_csrf_token()
        request.POST['csrf_token'] = token
        request.POST['index'] = 0
        site = make_site()
        site['page'] = context = testing.DummyResource()
        site.__acl__ = [(None, 1, (None,))]
        context.__acl__ = [(None, 1, (None,)),
                           (None, 2, (None,))]
        user = DummyUser(1, u'john')
        user2 = DummyUser(2, u'mary')
        site['principals']['users']['john'] = user
        site.__objectmap__ = DummyObjectMap({1:user, 2:user2})
        inst = self._makeOne(context, request)
        resp = inst()
        self.assertEqual(resp['parent_acl'], [(None, u'john', (None,))])
        self.assertEqual(resp['users'], [(1, u'john')])
        self.assertEqual(resp['groups'], [('system.Everyone',
                                          'system.Everyone'),
                                          ('system.Authenticated',
                                          'system.Authenticated')])
        self.assertEqual(resp['local_acl'], [(None, u'mary', (None,)),
                                             (None, u'john', (None,))])
        self.assertEqual(resp['permissions'], ['-- ALL --'])
        self.assertEqual(resp['inheriting'], 'enabled')
        self.assertEqual(request.sdiapi.flashed, 'ACE moved down')

class TestRemove(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _makeOne(self, context, request):
        from ..acl import ACLEditViews
        return ACLEditViews(context, request).remove

    def test_view(self):
        from ....testing import make_site
        request = testing.DummyRequest()
        request.sdiapi = DummySDIAPI()
        token = request.session.new_csrf_token()
        request.POST['csrf_token'] = token
        request.POST['index'] = 0
        site = make_site()
        site['page'] = context = testing.DummyResource()
        site.__acl__ = [(None, 1, (None,))]
        context.__acl__ = [(None, 1, (None,)),
                           (None, 2, (None,))]
        user = DummyUser(1, u'john')
        user2 = DummyUser(2, u'mary')
        site['principals']['users']['john'] = user
        site.__objectmap__ = DummyObjectMap({1:user, 2:user2})
        inst = self._makeOne(context, request)
        resp = inst()
        self.assertEqual(resp['parent_acl'], [(None, u'john', (None,))])
        self.assertEqual(resp['users'], [(1, u'john')])
        self.assertEqual(resp['groups'], [('system.Everyone',
                                          'system.Everyone'),
                                          ('system.Authenticated',
                                          'system.Authenticated')])
        self.assertEqual(resp['local_acl'], [(None, u'mary', (None,))])
        self.assertEqual(resp['permissions'], ['-- ALL --'])
        self.assertEqual(resp['inheriting'], 'enabled')
        self.assertEqual(request.sdiapi.flashed, 'ACE removed')

class TestAdd(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _makeOne(self, context, request):
        from ..acl import ACLEditViews
        return ACLEditViews(context, request).add

    def test_add(self):
        from ....testing import make_site
        request = testing.DummyRequest()
        request.sdiapi = DummySDIAPI()
        request.POST = DummyPost(getall_result=('test',))
        token = request.session.get_csrf_token()
        request.params['csrf_token'] = token
        request.POST['verb'] = 'allow'
        request.POST['principal'] = '1'
        request.POST['permissions'] = 'test'
        site = make_site()
        site['page'] = context = testing.DummyResource()
        site.__acl__ = [(None, 1, (None,))]
        context.__acl__ = [(None, 1, (None,)),
                           (None, 2, (None,))]
        user = DummyUser(1, u'john')
        user2 = DummyUser(2, u'mary')
        site['principals']['users']['john'] = user
        site.__objectmap__ = DummyObjectMap({1:user, 2:user2})
        inst = self._makeOne(context, request)
        resp = inst()
        self.assertEqual(resp['parent_acl'], [(None, u'john', (None,))])
        self.assertEqual(resp['users'], [(1, u'john')])
        self.assertEqual(resp['groups'], [('system.Everyone',
                                          'system.Everyone'),
                                          ('system.Authenticated',
                                          'system.Authenticated')])
        self.assertEqual(resp['local_acl'], [(None, u'john', (None,)),
                                             (None, u'mary', (None,)),
                                             ('allow', u'john', ('test',))])
        self.assertEqual(resp['permissions'], ['-- ALL --'])
        self.assertEqual(resp['inheriting'], 'enabled')
        self.assertEqual(request.sdiapi.flashed, 'New ACE added')

    def test_add_no_principal_selected(self):
        from ....testing import make_site
        request = testing.DummyRequest()
        request.sdiapi = DummySDIAPI()
        request.POST = DummyPost(getall_result=('test',))
        token = request.session.get_csrf_token()
        request.params['csrf_token'] = token
        request.POST['verb'] = 'allow'
        request.POST['principal'] = ''
        request.POST['permissions'] = 'test'
        site = make_site()
        site['page'] = context = testing.DummyResource()
        site.__acl__ = [(None, 1, (None,))]
        context.__acl__ = [(None, 1, (None,)),
                           (None, 2, (None,))]
        user = DummyUser(1, u'john')
        user2 = DummyUser(2, u'mary')
        site['principals']['users']['john'] = user
        site.__objectmap__ = DummyObjectMap({1:user, 2:user2})
        inst = self._makeOne(context, request)
        resp = inst()
        self.assertEqual(resp['parent_acl'], [(None, u'john', (None,))])
        self.assertEqual(resp['users'], [(1, u'john')])
        self.assertEqual(resp['groups'], [('system.Everyone',
                                          'system.Everyone'),
                                          ('system.Authenticated',
                                          'system.Authenticated')])
        self.assertEqual(resp['local_acl'], [(None, u'john', (None,)),
                                             (None, u'mary', (None,))])
        self.assertEqual(resp['permissions'], ['-- ALL --'])
        self.assertEqual(resp['inheriting'], 'enabled')
        self.assertEqual(request.session['_f_error'],
                         ['No principal selected'])

    def test_add_unknown_user(self):
        from ....testing import make_site
        request = testing.DummyRequest()
        request.sdiapi = DummySDIAPI()
        request.POST = DummyPost(getall_result=('test',))
        token = request.session.get_csrf_token()
        request.params['csrf_token'] = token
        request.POST['verb'] = 'allow'
        request.POST['principal'] = '3'
        request.POST['permissions'] = 'test'
        site = make_site()
        site['page'] = context = testing.DummyResource()
        site.__acl__ = [(None, 1, (None,))]
        context.__acl__ = [(None, 1, (None,)),
                           (None, 2, (None,))]
        user = DummyUser(1, u'john')
        user2 = DummyUser(2, u'mary')
        site['principals']['users']['john'] = user
        site.__objectmap__ = DummyObjectMap({1:user, 2:user2})
        inst = self._makeOne(context, request)
        resp = inst()
        self.assertEqual(resp['parent_acl'], [(None, u'john', (None,))])
        self.assertEqual(resp['users'], [(1, u'john')])
        self.assertEqual(resp['groups'], [('system.Everyone',
                                          'system.Everyone'),
                                          ('system.Authenticated',
                                          'system.Authenticated')])
        self.assertEqual(resp['local_acl'], [(None, u'john', (None,)),
                                             (None, u'mary', (None,))])
        self.assertEqual(resp['permissions'], ['-- ALL --'])
        self.assertEqual(resp['inheriting'], 'enabled')
        self.assertEqual(request.session['_f_error'],
                         ['Unknown user or group when adding ACE'])

class TestInherit(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _makeOne(self, context, request):
        from ..acl import ACLEditViews
        return ACLEditViews(context, request).inherit

    def test_inherit_enabled(self):
        from ....testing import make_site
        request = testing.DummyRequest()
        request.sdiapi = DummySDIAPI()
        token = request.session.new_csrf_token()
        request.POST['csrf_token'] = token
        request.POST['inherit'] = 'enabled'
        site = make_site()
        site['page'] = context = testing.DummyResource()
        site.__acl__ = [(None, 1, (None,))]
        context.__acl__ = [(None, 1, (None,)),
                           (None, 2, (None,))]
        user = DummyUser(1, u'john')
        user2 = DummyUser(2, u'mary')
        site['principals']['users']['john'] = user
        site.__objectmap__ = DummyObjectMap({1:user, 2:user2})
        inst = self._makeOne(context, request)
        resp = inst()
        self.assertEqual(resp['parent_acl'], [(None, u'john', (None,))])
        self.assertEqual(resp['users'], [(1, u'john')])
        self.assertEqual(resp['groups'], [('system.Everyone',
                                          'system.Everyone'),
                                          ('system.Authenticated',
                                          'system.Authenticated')])
        self.assertEqual(resp['local_acl'], [(None, u'john', (None,)),
                                             (None, u'mary', (None,))])
        self.assertEqual(resp['permissions'], ['-- ALL --'])
        self.assertEqual(resp['inheriting'], 'enabled')
        self.assertEqual(request.sdiapi.flashed,
                         'ACL will inherit from parent')

    def test_inherit_disabled(self):
        from ....testing import make_site
        request = testing.DummyRequest()
        request.sdiapi = DummySDIAPI()
        token = request.session.new_csrf_token()
        request.POST['csrf_token'] = token
        request.POST['inherit'] = 'disabled'
        site = make_site()
        site['page'] = context = testing.DummyResource()
        site.__acl__ = [(None, 1, (None,))]
        context.__acl__ = [(None, 1, (None,)),
                           (None, 2, (None,))]
        user = DummyUser(1, u'john')
        user2 = DummyUser(2, u'mary')
        site['principals']['users']['john'] = user
        site.__objectmap__ = DummyObjectMap({1:user, 2:user2})
        inst = self._makeOne(context, request)
        resp = inst()
        self.assertEqual(resp['parent_acl'], [(None, u'john', (None,))])
        self.assertEqual(resp['users'], [(1, u'john')])
        self.assertEqual(resp['groups'], [('system.Everyone',
                                          'system.Everyone'),
                                          ('system.Authenticated',
                                          'system.Authenticated')])
        self.assertEqual(resp['local_acl'], [(None, u'john', (None,)),
                                             (None, u'mary', (None,))])
        self.assertEqual(resp['permissions'], ['-- ALL --'])
        self.assertEqual(resp['inheriting'], 'disabled')
        self.assertEqual(request.sdiapi.flashed,
                         'ACL will *not* inherit from parent')

class DummyUser(object):
    def __init__(self, oid, name):
        self.__oid__ = oid
        self.__name__ = name

class DummyPost(dict):
    def __init__(self, getall_result=(), get_result=None):
        self.getall_result = getall_result
        self.get_result = get_result

    def getall(self, name): # pragma: no cover
        return self.getall_result

    def get(self, name, default=None):
        if self.get_result is None: # pragma: no cover
            return default
        return self.get_result

class DummyObjectMap(object):
    def __init__(self, objectmap):
        self.objectmap = objectmap
    def object_for(self, oid):
        return self.objectmap.get(oid, None)

class DummySDIAPI(object):
    def flash_with_undo(self, message):
        self.flashed = (message)

