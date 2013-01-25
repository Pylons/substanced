import unittest
from pyramid import testing
import colander
from zope.interface import implementer

class TestPrincipals(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
        
    def _makeOne(self):
        from .. import Principals
        return Principals()

    def test___sdi_addable__True(self):
        intr = {'content_type':'Users'}
        inst = self._makeOne()
        self.assertTrue(inst.__sdi_addable__(None, intr))

    def test___sdi_addable__False(self):
        intr = {'content_type':'Wrong'}
        inst = self._makeOne()
        self.assertFalse(inst.__sdi_addable__(None, intr))

    def test_after_create(self):
        inst = self._makeOne()
        D = {}
        def add(name, val, registry=None):
            D[name] = val
        inst.add = add
        ob = testing.DummyResource()
        content = DummyContentRegistry(ob)
        registry = testing.DummyResource()
        registry.content = content
        inst.after_create(None, registry)
        self.assertEqual(D['users'], ob)
        self.assertEqual(D['groups'], ob)
        self.assertEqual(D['resets'], ob)

    def test_add_user(self):
        inst = self._makeOne()
        users = inst['users'] = testing.DummyResource()
        ob = testing.DummyResource()
        content = DummyContentRegistry(ob)
        self.config.registry.content = content
        user = inst.add_user('login', 'password')
        self.assertTrue('login' in users)
        self.assertEqual(user.__name__, 'login')

    def test_add_group(self):
        inst = self._makeOne()
        groups = inst['groups'] = testing.DummyResource()
        ob = testing.DummyResource()
        content = DummyContentRegistry(ob)
        self.config.registry.content = content
        group = inst.add_group('groupname')
        self.assertTrue('groupname' in groups)
        self.assertEqual(group.__name__, 'groupname')

    def test_add_reset(self):
        from .. import UserToPasswordReset
        ob = testing.DummyResource()
        content = DummyContentRegistry(ob)
        self.config.registry.content = content
        resets = testing.DummyResource()
        inst = self._makeOne()
        objectmap = DummyObjectMap()
        inst.__objectmap__ = objectmap
        inst.add('resets', resets)
        user = testing.DummyResource()
        reset = inst.add_reset(user)
        self.assertEqual(
            objectmap.connections,
            [(user, reset, UserToPasswordReset)])
        self.assertTrue(reset.__acl__)
        self.assertEqual(len(inst), 1)

class TestUsers(unittest.TestCase):
    def _makeOne(self):
        from .. import Users
        return Users()

    def test___sdi_addable__True(self):
        intr = {'content_type':'User'}
        inst = self._makeOne()
        self.assertTrue(inst.__sdi_addable__(None, intr))

    def test___sdi_addable__False(self):
        intr = {'content_type':'Wrong'}
        inst = self._makeOne()
        self.assertFalse(inst.__sdi_addable__(None, intr))

class TestPasswordResets(unittest.TestCase):
    def _makeOne(self):
        from .. import PasswordResets
        return PasswordResets()

    def test___sdi_addable__True(self):
        intr = {'content_type':'Password Reset'}
        inst = self._makeOne()
        self.assertTrue(inst.__sdi_addable__(None, intr))

    def test___sdi_addable__False(self):
        intr = {'content_type':'Wrong'}
        inst = self._makeOne()
        self.assertFalse(inst.__sdi_addable__(None, intr))

class TestGroups(unittest.TestCase):
    def _makeOne(self):
        from .. import Groups
        return Groups()

    def test___sdi_addable__True(self):
        intr = {'content_type':'Group'}
        inst = self._makeOne()
        self.assertTrue(inst.__sdi_addable__(None, intr))

    def test___sdi_addable__False(self):
        intr = {'content_type':'Wrong'}
        inst = self._makeOne()
        self.assertFalse(inst.__sdi_addable__(None,  intr))

class Test_groupname_validator(unittest.TestCase):
    def _makeOne(self, node, kw):
        from .. import groupname_validator
        return groupname_validator(node, kw)
    
    def _makeKw(self):
        request = testing.DummyRequest()
        context = DummyFolder()
        principals = DummyFolder()
        principals.__is_service__ = True
        groups = DummyFolder()
        users = DummyFolder()
        context['principals'] = principals
        context['principals']['groups'] = groups
        context['principals']['users'] = users
        request.context = context
        return dict(request=request, context=context)

    def test_it_not_adding_with_exception(self):
        kw = self._makeKw()
        request = kw['request']
        request.registry.content = DummyContentRegistry(True)
        kw['request'].context['abc'] = testing.DummyResource()
        def check_name(*arg, **kw):
            raise Exception('fred')
        kw['context']['principals']['groups'].check_name = check_name
        node = object()
        v = self._makeOne(node, kw)
        self.assertRaises(colander.Invalid, v, node, 'abc')

    def test_it_adding_with_exception(self):
        kw = self._makeKw()
        request = kw['request']
        request.registry.content = DummyContentRegistry(False)
        request.context['abc'] = testing.DummyResource()
        node = object()
        v = self._makeOne(node, kw)
        self.assertRaises(colander.Invalid, v, node, 'abc')

    def test_it_adding_with_exception_exists_in_users(self):
        kw = self._makeKw()
        request = kw['request']
        request.registry.content = DummyContentRegistry(False)
        principals = kw['context']['principals']
        principals['users']['abc'] = testing.DummyResource()
        node = object()
        v = self._makeOne(node, kw)
        self.assertRaises(colander.Invalid, v, node, 'abc')

class Test_members_choices(unittest.TestCase):
    def _makeOne(self, context, request):
        from .. import members_choices
        return members_choices(context, request)

    def test_it(self):
        from ...testing import make_site
        site = make_site()
        user = testing.DummyResource()
        user.__oid__ = 1
        site['principals']['users']['user'] = user
        request = testing.DummyRequest()
        result = self._makeOne(site, request)
        self.assertEqual(result, [(1, 'user')])

    def test_it_no_principals_service(self):
        site = testing.DummyResource()
        request = testing.DummyRequest()
        result = self._makeOne(site, request)
        self.assertEqual(result, ())

class TestGroup(unittest.TestCase):
    def _makeOne(self, description=''):
        from .. import Group
        return Group(description)

    def test_ctor(self):
        inst = self._makeOne('abc')
        self.assertEqual(inst.description, 'abc')

class Test_login_validator(unittest.TestCase):
    def _makeOne(self, node, kw):
        from .. import login_validator
        return login_validator(node, kw)

    def test_adding_check_name_fails(self):
        from ...testing import make_site
        site = make_site()
        user = testing.DummyResource()
        user.__oid__ = 1
        def check_name(v): raise ValueError(v)
        user.check_name = check_name
        site['principals']['users']['user'] = user
        request = testing.DummyRequest()
        request.context = user
        request.registry.content = DummyContentRegistry(False)
        kw = dict(request=request)
        inst = self._makeOne(None, kw)
        self.assertRaises(colander.Invalid, inst, None, 'name')

    def test_not_adding_check_name_fails(self):
        from ...testing import make_site
        site = make_site()
        user = testing.DummyResource()
        user.__oid__ = 1
        def check_name(*arg):
            raise ValueError('a')
        users = site['principals']['users']
        users['user'] = user
        users.check_name = check_name
        request = testing.DummyRequest()
        request.context = user
        request.registry.content = DummyContentRegistry(True)
        kw = dict(request=request)
        inst = self._makeOne(None, kw)
        self.assertRaises(colander.Invalid, inst, None, 'newname')

    def test_not_adding_newname_same_as_old(self):
        from ...testing import make_site
        site = make_site()
        user = testing.DummyResource()
        user.__oid__ = 1
        def check_name(v): raise ValueError(v)
        user.check_name = check_name
        site['principals']['users']['user'] = user
        request = testing.DummyRequest()
        request.context = user
        request.registry.content = DummyContentRegistry(True)
        kw = dict(request=request)
        inst = self._makeOne(None, kw)
        self.assertEqual(inst(None, 'user'), None)

    def test_groupname_exists(self):
        from ...testing import make_site
        site = make_site()
        user = testing.DummyResource()
        user.__oid__ = 1
        def check_name(v): raise ValueError(v)
        user.check_name = check_name
        group = testing.DummyResource()
        site['principals']['users']['user'] = user
        site['principals']['groups']['group'] = group
        request = testing.DummyRequest()
        request.context = user
        request.registry.content = DummyContentRegistry(True)
        kw = dict(request=request)
        inst = self._makeOne(None, kw)
        self.assertRaises(colander.Invalid, inst, None, 'group')

class Test_groups_choices(unittest.TestCase):
    def _makeOne(self, context, request):
        from .. import groups_choices
        return groups_choices(context, request)

    def test_it(self):
        from ...testing import make_site
        site = make_site()
        group = testing.DummyResource()
        group.__oid__ = 1
        site['principals']['groups']['group'] = group
        request = testing.DummyRequest()
        result = self._makeOne(site, request)
        self.assertEqual(result, [(1, 'group')])

    def test_it_no_principals_service(self):
        site = testing.DummyResource()
        request = testing.DummyRequest()
        result = self._makeOne(site, request)
        self.assertEqual(result, ())

class TestUser(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
        
    def _makeOne(self, password, email=''):
        from .. import User
        return User(password, email)

    def test___dump__(self):
        inst = self._makeOne('abc')
        result = inst.__dump__()
        self.assertTrue(inst.pwd_manager.check(result['password'], 'abc'))

    def test_check_password(self):
        inst = self._makeOne('abc')
        self.assertTrue(inst.check_password('abc'))
        self.assertFalse(inst.check_password('abcdef'))

    def test_set_password(self):
        inst = self._makeOne('abc')
        inst.set_password('abcdef')
        self.assertTrue(inst.pwd_manager.check(inst.password, 'abcdef'))

    def test_email_password_reset(self):
        from ...testing import make_site
        from pyramid_mailer import get_mailer
        site = make_site()
        principals = site['principals']
        principals['resets'] = testing.DummyResource()
        def add_reset(user):
            self.assertEqual(user, inst)
        principals.add_reset = add_reset
        request = testing.DummyRequest()
        request.sdiapi = DummySDIAPI()
        request.root = site
        self.config.include('pyramid_mailer.testing')
        inst = self._makeOne('password')
        principals['users']['user'] = inst
        inst.email_password_reset(request)
        self.assertTrue(get_mailer(request).outbox)

class Test_groupfinder(unittest.TestCase):
    def _callFUT(self, userid, request):
        from .. import groupfinder
        return groupfinder(userid, request)

    def test_with_no_objectmap(self):
        from ...interfaces import IFolder
        request = testing.DummyRequest()
        context = testing.DummyResource(__provides__=IFolder)
        request.context = context
        result = self._callFUT(1, request)
        self.assertEqual(result, None)
    
    def test_with_objectmap_no_user(self):
        from ...interfaces import IFolder
        request = testing.DummyRequest()
        context = testing.DummyResource(__provides__=IFolder)
        omap = testing.DummyResource()
        omap.object_for = lambda *arg: None
        context.__objectmap__ = omap
        request.context = context
        result = self._callFUT(1, request)
        self.assertEqual(result, None)
        
    def test_garden_path(self):
        from ...interfaces import IFolder
        request = testing.DummyRequest()
        context = testing.DummyResource(__provides__=IFolder)
        omap = testing.DummyResource()
        user = testing.DummyResource()
        user.groupids = (1,2)
        omap.object_for = lambda *arg: user
        context.__objectmap__ = omap
        request.context = context
        result = self._callFUT(1, request)
        self.assertEqual(result, (1,2))

class TestPasswordReset(unittest.TestCase):
    def _makeOne(self):
        from .. import PasswordReset
        return PasswordReset()

    def test_reset_password(self):
        from ...interfaces import IFolder
        parent = testing.DummyResource(__provides__=IFolder)
        user = testing.DummyResource()
        def set_password(password):
            user.password = password
        user.set_password = set_password
        objectmap = DummyObjectMap((user,))
        inst = self._makeOne()
        parent.__objectmap__ = objectmap
        parent['reset'] = inst
        inst.reset_password('password')
        self.assertEqual(user.password, 'password')
        self.assertFalse('reset' in parent)

        
from ...interfaces import IFolder

@implementer(IFolder)
class DummyFolder(testing.DummyResource):
    def check_name(self, value):
        if value in self:
            raise KeyError(value)

class DummyObjectMap(object):
    def __init__(self, result=()):
        self.result = result
        self.connections = []

    def sources(self, object, reftype):
        return self.result

    def connect(self, source, target, reftype):
        self.connections.append((source, target, reftype))

    def add(self, node, path_tuple, duplicating=False, moving=False):
        pass

class DummyContentRegistry(object):
    def __init__(self, result):
        self.result = result

    def istype(self, context, type):
        return self.result

    def create(self, name, *arg, **kw):
        return self.result
    
class DummySDIAPI(object):
    def mgmt_path(self, *arg, **kw):
        return '/mgmt_path'
