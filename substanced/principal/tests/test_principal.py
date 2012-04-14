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
        inst.add_user('login', 'password')
        self.assertTrue('login' in inst)

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

    def sources(self, object, reftype):
        return self.result

    def connect(self, source, target, reftype):
        self.connections.append((source, target, reftype))

    def disconnect(self, source, target, reftype):
        self.disconnections.append((source, target, reftype))
    
