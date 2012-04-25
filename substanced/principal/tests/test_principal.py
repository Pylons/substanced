import unittest
from pyramid import testing
import colander
from zope.interface import (
    alsoProvides,
    implementer,
    )

class TestPrincipals(unittest.TestCase):
    def _makeOne(self):
        from .. import Principals
        return Principals()

    def test_ctor(self):
        inst = self._makeOne()
        self.assertTrue('users' in inst)
        self.assertTrue('groups' in inst)
        
class TestUsers(unittest.TestCase):
    def _makeOne(self):
        from .. import Users
        return Users()

    def test_add_user(self):
        inst = self._makeOne()
        user = inst.add_user('login', 'password')
        self.assertTrue('login' in inst)
        self.assertEqual(user.__name__, 'login')

class TestGroups(unittest.TestCase):
    def _makeOne(self):
        from .. import Groups
        return Groups()

    def test_add_group(self):
        inst = self._makeOne()
        group = inst.add_group('groupname')
        self.assertTrue('groupname' in inst)
        self.assertEqual(group.__name__, 'groupname')

class Test_groupname_validator(unittest.TestCase):
    def _makeOne(self, node, kw):
        from .. import groupname_validator
        return groupname_validator(node, kw)
    
    def _makeKw(self):
        request = testing.DummyRequest()
        context = DummyFolder()
        services = DummyFolder()
        principals = DummyFolder()
        groups = DummyFolder()
        users = DummyFolder()
        context['__services__'] = services
        context['__services__']['principals'] = principals
        context['__services__']['principals']['groups'] = groups
        context['__services__']['principals']['users'] = users
        request.services = services
        request.context = context
        return dict(request=request)

    def test_it_not_adding_with_exception(self):
        kw = self._makeKw()
        kw['request'].context['abc'] = testing.DummyResource()
        node = object()
        v = self._makeOne(node, kw)
        self.assertRaises(colander.Invalid, v, node, 'abc')

    def test_it_adding_with_exception(self):
        from ...interfaces import IGroup
        kw = self._makeKw()
        context = kw['request'].context
        alsoProvides(context, IGroup)
        services = kw['request'].services
        services['principals']['groups']['abc'] = testing.DummyResource()
        node = object()
        v = self._makeOne(node, kw)
        self.assertRaises(colander.Invalid, v, node, 'abc')

    def test_it_adding_with_exception_exists_in_users(self):
        from ...interfaces import IGroup
        kw = self._makeKw()
        context = kw['request'].context
        alsoProvides(context, IGroup)
        services = kw['request'].services
        services['principals']['users']['abc'] = testing.DummyResource()
        node = object()
        v = self._makeOne(node, kw)
        self.assertRaises(colander.Invalid, v, node, 'abc')

class Test_members_widget(unittest.TestCase):
    def _makeOne(self, node, kw):
        from .. import members_widget
        return members_widget(node, kw)

    def test_it(self):
        from ...testing import make_site
        site = make_site()
        user = testing.DummyResource()
        user.__objectid__ = 1
        site['__services__']['principals']['users']['user'] = user
        request = testing.DummyRequest()
        request.context = site
        kw = dict(request=request)
        result = self._makeOne(None, kw)
        self.assertEqual(result.values, [('1', 'user')])

class TestGroup(unittest.TestCase):
    def _makeOne(self, description=''):
        from .. import Group
        return Group(description)

    def _makeParent(self):
        parent = DummyFolder()
        parent['__services__'] = DummyFolder()
        objectmap = DummyObjectMap()
        parent['__services__']['objectmap'] = objectmap
        parent.objectmap = objectmap
        return parent

    def test_get_properties(self):
        inst = self._makeOne('desc')
        parent = self._makeParent()
        parent['name'] = inst
        props = inst.get_properties()
        self.assertEqual(props['description'], 'desc')
        self.assertEqual(props['members'], [])
        self.assertEqual(props['name'], 'name')

    def test_set_properties(self):
        inst = self._makeOne()
        parent = self._makeParent()
        parent['oldname'] = inst
        inst.set_properties({'description':'desc', 'name':'name', 'members':()})
        self.assertEqual(inst.description, 'desc')
        self.assertTrue('name' in parent)

    def test_get_memberids(self):
        parent = self._makeParent()
        inst = self._makeOne()
        parent['name'] = inst
        self.assertEqual(inst.get_memberids(), ())

    def test_get_members(self):
        parent = self._makeParent()
        inst = self._makeOne()
        parent['name'] = inst
        self.assertEqual(inst.get_members(), ())

    def test_connect(self):
        from .. import UserToGroup
        parent = self._makeParent()
        inst = self._makeOne()
        parent['name'] = inst
        inst.connect(1, 2)
        self.assertEqual(parent.objectmap.connections,
                         [(1, inst, UserToGroup), (2, inst, UserToGroup)])

    def test_disconnect(self):
        from .. import UserToGroup
        parent = self._makeParent()
        inst = self._makeOne()
        parent['name'] = inst
        inst.disconnect(1, 2)
        self.assertEqual(parent.objectmap.disconnections,
                         [(1, inst, UserToGroup), (2, inst, UserToGroup)])

class Test_login_validator(unittest.TestCase):
    def _makeOne(self, node, kw):
        from .. import login_validator
        return login_validator(node, kw)

    def test_adding_check_name_fails(self):
        from ...testing import make_site
        site = make_site()
        user = testing.DummyResource()
        user.__objectid__ = 1
        def check_name(v): raise ValueError(v)
        user.check_name = check_name
        site['__services__']['principals']['users']['user'] = user
        request = testing.DummyRequest()
        request.context = user
        kw = dict(request=request)
        inst = self._makeOne(None, kw)
        self.assertRaises(colander.Invalid, inst, None, 'name')

    def test_not_adding_check_name_fails(self):
        from ...testing import make_site
        from ...interfaces import IUser
        site = make_site()
        user = testing.DummyResource(__provides__=IUser)
        user.__objectid__ = 1
        def check_name(*arg):
            raise ValueError('a')
        users = site['__services__']['principals']['users']
        users['user'] = user
        users.check_name = check_name
        request = testing.DummyRequest()
        request.context = user
        kw = dict(request=request)
        inst = self._makeOne(None, kw)
        self.assertRaises(colander.Invalid, inst, None, 'newname')

    def test_not_adding_newname_same_as_old(self):
        from ...testing import make_site
        from ...interfaces import IUser
        site = make_site()
        user = testing.DummyResource(__provides__=IUser)
        user.__objectid__ = 1
        def check_name(v): raise ValueError(v)
        user.check_name = check_name
        site['__services__']['principals']['users']['user'] = user
        request = testing.DummyRequest()
        request.context = user
        kw = dict(request=request)
        inst = self._makeOne(None, kw)
        self.assertEqual(inst(None, 'user'), None)

    def test_groupname_exists(self):
        from ...testing import make_site
        from ...interfaces import IUser
        site = make_site()
        user = testing.DummyResource(__provides__=IUser)
        user.__objectid__ = 1
        def check_name(v): raise ValueError(v)
        user.check_name = check_name
        site['__services__']['principals']['users']['user'] = user
        site['__services__']['principals']['groups']['group'] = user
        request = testing.DummyRequest()
        request.context = user
        kw = dict(request=request)
        inst = self._makeOne(None, kw)
        self.assertRaises(colander.Invalid, inst, None, 'group')

class Test_groups_widget(unittest.TestCase):
    def _makeOne(self, node, kw):
        from .. import groups_widget
        return groups_widget(node, kw)

    def test_it(self):
        from ...testing import make_site
        site = make_site()
        group = testing.DummyResource()
        group.__objectid__ = 1
        site['__services__']['principals']['groups']['group'] = group
        request = testing.DummyRequest()
        request.context = site
        kw = dict(request=request)
        result = self._makeOne(None, kw)
        self.assertEqual(result.values, [('1', 'group')])

class TestUser(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
        
    def _makeOne(self, password, email=''):
        from .. import User
        return User(password, email)

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
        principals = site['__services__']['principals']
        resets = principals['resets'] = testing.DummyResource()
        def add_reset(user):
            self.assertEqual(user, inst)
        resets.add_reset = add_reset
        request = testing.DummyRequest()
        request.mgmt_path = lambda *arg: '/mgmt'
        request.root = site
        self.config.include('pyramid_mailer.testing')
        inst = self._makeOne('password')
        principals['users']['user'] = inst
        inst.email_password_reset(request)
        self.assertTrue(get_mailer(request).outbox)

    def test_get_properties(self):
        inst = self._makeOne('abc', 'email')
        inst.__name__ = 'fred'
        inst.get_groupids = lambda: [1,2]
        self.assertEqual(inst.get_properties(),
                         {'email':'email', 'login':'fred', 'groups':['1', '2']})
        
    def test_set_properties_newname_same_as_old(self):
        from ...testing import make_site
        parent = make_site()
        inst = self._makeOne('abc', 'email')
        parent['login'] = inst
        inst.get_groupids = lambda: [1,2]
        inst.set_properties({'login':'abc', 'email':'email2', 'groups':()})
        self.assertEqual(inst.__name__, 'abc')
        self.assertEqual(inst.email, 'email2')

    def test_set_properties_newname_different(self):
        from ...testing import make_site
        parent = make_site()
        inst = self._makeOne('abc', 'email')
        parent['login'] = inst
        inst.get_groupids = lambda: [1,2]
        inst.set_properties({'login':'newname', 'email':'email2', 'groups':()})
        self.assertTrue('newname' in parent)
        self.assertEqual(inst.__name__, 'newname')
        self.assertEqual(inst.email, 'email2')

    def test_set_properties_newgroups(self):
        from ...testing import make_site
        parent = make_site()
        inst = self._makeOne('abc', 'email')
        parent['login'] = inst
        inst.get_groupids = lambda: [1,2]
        connect_called = []
        def connect(*args):
            connect_called.append(True)
            self.assertEqual(args, (1,))
        inst.connect = connect
        inst.set_properties(
            {'login':'newname', 'email':'email2', 'groups':(1,)})
        self.assertTrue(connect_called)

    def test_get_groupids(self):
        from ...testing import make_site
        parent = make_site()
        parent['__services__'].replace('objectmap', DummyObjectMap(True))
        inst = self._makeOne('abc')
        parent['foo'] = inst
        self.assertEqual(inst.get_groupids(), True)

    def test_get_groups(self):
        from ...testing import make_site
        parent = make_site()
        parent['__services__'].replace('objectmap', DummyObjectMap(True))
        inst = self._makeOne('abc')
        parent['foo'] = inst
        self.assertEqual(inst.get_groups(), True)

    def test_connect(self):
        from .. import UserToGroup
        from ...testing import make_site
        parent = make_site()
        omap = DummyObjectMap(True)
        parent['__services__'].replace('objectmap', omap)
        inst = self._makeOne('abc')
        parent['foo'] = inst
        inst.connect(1, 2)
        self.assertEqual(omap.connections,
                         [(inst, 1, UserToGroup), (inst, 2, UserToGroup)])

    def test_disconnect_no_groups(self):
        from .. import UserToGroup
        from ...testing import make_site
        parent = make_site()
        omap = DummyObjectMap(True)
        parent['__services__'].replace('objectmap', omap)
        inst = self._makeOne('abc')
        inst.get_groupids = lambda: (1, 2)
        parent['foo'] = inst
        inst.disconnect()
        self.assertEqual(omap.disconnections,
                         [(inst, 1, UserToGroup), (inst, 2, UserToGroup)])
        
    def test_disconnect_with_groups(self):
        from .. import UserToGroup
        from ...testing import make_site
        parent = make_site()
        omap = DummyObjectMap(True)
        parent['__services__'].replace('objectmap', omap)
        inst = self._makeOne('abc')
        parent['foo'] = inst
        inst.disconnect(1,2)
        self.assertEqual(omap.disconnections,
                         [(inst, 1, UserToGroup), (inst, 2, UserToGroup)])

    def test__resolve_group_with_oid(self):
        from ...testing import make_site
        parent = make_site()
        omap = DummyObjectMap(True)
        parent['__services__'].replace('objectmap', omap)
        inst = self._makeOne('abc')
        g1 = testing.DummyResource()
        g1.__objectid__ = 1
        self.assertEqual(inst._resolve_group(g1), g1)

class Test_principal_added(unittest.TestCase):
    def _callFUT(self, principal, event):
        from .. import principal_added
        return principal_added(principal, event)

    def test_user_not_in_groups(self):
        from ...testing import make_site
        from ...interfaces import IUser
        site = make_site()
        user = testing.DummyResource(__provides__=IUser)
        site['user'] = user
        self._callFUT(user, None) # doesnt blow up

    def test_user_in_groups(self):
        from ...testing import make_site
        from ...interfaces import IUser
        site = make_site()
        groups = site['__services__']['principals']['groups']
        groups['user'] = testing.DummyResource()
        user = testing.DummyResource(__provides__=IUser)
        site['user'] = user
        self.assertRaises(ValueError, self._callFUT, user, None)

    def test_group_not_in_users(self):
        from ...testing import make_site
        site = make_site()
        group = testing.DummyResource()
        site['groups'] = group
        self._callFUT(group, None) # doesnt blow up

    def test_group_in_users(self):
        from ...testing import make_site
        site = make_site()
        users = site['__services__']['principals']['users']
        users['group'] = testing.DummyResource()
        group = testing.DummyResource()
        site['group'] = group
        self.assertRaises(ValueError, self._callFUT, group, None)

class Test_groupfinder(unittest.TestCase):
    def _callFUT(self, userid, request):
        from .. import groupfinder
        return groupfinder(userid, request)

    def test_with_no_objectmap(self):
        from ...interfaces import IFolder
        request = testing.DummyRequest()
        context = testing.DummyResource(__provides__=IFolder)
        services = testing.DummyResource()
        context['__services__'] = services
        request.context = context
        result = self._callFUT(1, request)
        self.assertEqual(result, None)
    
    def test_with_objectmap_no_user(self):
        from ...interfaces import IFolder
        request = testing.DummyRequest()
        context = testing.DummyResource(__provides__=IFolder)
        omap = testing.DummyResource()
        omap.object_for = lambda *arg: None
        services = testing.DummyResource()
        services['objectmap'] = omap
        context['__services__'] = services
        request.context = context
        result = self._callFUT(1, request)
        self.assertEqual(result, None)
        
    def test_garden_path(self):
        from ...interfaces import IFolder
        request = testing.DummyRequest()
        context = testing.DummyResource(__provides__=IFolder)
        omap = testing.DummyResource()
        user = testing.DummyResource()
        user.get_groupids = lambda *arg: (1,2)
        omap.object_for = lambda *arg: user
        services = testing.DummyResource()
        services['objectmap'] = omap
        context['__services__'] = services
        request.context = context
        result = self._callFUT(1, request)
        self.assertEqual(result, (1,2))

class TestPasswordResets(unittest.TestCase):
    def _makeOne(self):
        from .. import PasswordResets
        return PasswordResets()

    def test_add_reset(self):
        from .. import UserToPasswordReset
        inst = self._makeOne()
        objectmap = DummyObjectMap()
        services = testing.DummyResource()
        inst.add('__services__', services, allow_services=True)
        services['objectmap'] = objectmap
        user = testing.DummyResource()
        reset = inst.add_reset(user)
        self.assertEqual(
            objectmap.connections,
            [(user, reset, UserToPasswordReset)])
        self.assertTrue(reset.__acl__)
        self.assertEqual(len(inst), 2)
        
from ...interfaces import IFolder

@implementer(IFolder)
class DummyFolder(testing.DummyResource):
    def check_name(self, value):
        if value in self:
            raise KeyError(value)

    def rename(self, oldname, newname):
        old = self[oldname]
        del self[oldname]
        self[newname] = old

class DummyObjectMap(object):
    def __init__(self, result=()):
        self.result = result
        self.connections = []
        self.disconnections = []

    def object_for(self, oid):
        return oid

    def sourceids(self, object, reftype):
        return self.result

    def targetids(self, object, reftype):
        return self.result

    def sources(self, object, reftype):
        return self.result

    def targets(self, object, reftype):
        return self.result

    def connect(self, source, target, reftype):
        self.connections.append((source, target, reftype))

    def disconnect(self, source, target, reftype):
        self.disconnections.append((source, target, reftype))
    
