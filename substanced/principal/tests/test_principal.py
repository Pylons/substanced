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

class TestMembersWidget(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
        
    def _makeOne(self):
        from .. import MembersWidget
        return MembersWidget()

    def test_serialize(self):
        inst = self._makeOne()
        result = inst.serialize(None, None)
        self.assertTrue('no members' in result.lower())

    def test_deserialize(self):
        inst = self._makeOne()
        result = inst.deserialize(None, None)
        self.assertTrue(result is colander.null)
        
from ...interfaces import IFolder

@implementer(IFolder)
class DummyFolder(testing.DummyResource):
    def check_name(self, value):
        if value in self:
            raise KeyError(value)
