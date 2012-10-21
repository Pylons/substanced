import unittest
from pyramid import testing

from zope.interface import Interface
from zope.interface import alsoProvides

class Test_get_interfaces(unittest.TestCase):
    def _callFUT(self, object, default):
        from ..discriminators import get_interfaces
        return get_interfaces(object, default)

    def test_it(self):
        context = testing.DummyModel()
        class Dummy1(Interface):
            pass
        class Dummy2(Interface):
            pass
        alsoProvides(context, Dummy1)
        alsoProvides(context, Dummy2)
        wrapper = DummyContentViewWrapper(context, None)
        result = self._callFUT(wrapper, None)
        self.assertEqual(len(result), 4)
        self.assertTrue(Dummy1 in result)
        self.assertTrue(Dummy2 in result)
        self.assertTrue(Interface in result)
        self.assertTrue(testing.DummyModel in result)

class Test_get_containment(unittest.TestCase):
    def test_it(self):
        from ..discriminators import get_containment
        class Dummy1(Interface):
            pass
        class Dummy2(Interface):
            pass
        root = testing.DummyModel()
        alsoProvides(root, Dummy1)
        context = testing.DummyModel()
        alsoProvides(context, Dummy2)
        root['foo'] = context
        wrapper = DummyContentViewWrapper(context, None)
        result = get_containment(wrapper, None)
        self.assertEqual(len(result), 4)
        self.assertTrue(Dummy1 in result)
        self.assertTrue(Dummy2 in result)
        self.assertTrue(Interface in result)
        self.assertTrue(testing.DummyModel in result) 

class TestAllowedDiscriminator(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
        
    def _makeOne(self, permissions=None):
        from ..discriminators import AllowedDiscriminator
        return AllowedDiscriminator(permissions)

    def test_it_namedpermission(self):
        inst = self._makeOne('view')
        context = testing.DummyModel()
        wrapper = DummyContentViewWrapper(context, None)
        result = inst(wrapper, None)
        self.assertEqual(result, [('system.Everyone', 'view')])

    def test_it_namedpermission_notpermitted(self):
        from pyramid.interfaces import IAuthenticationPolicy
        self.config.testing_securitypolicy(permissive=False)
        from ..discriminators import NoWay
        pol = self.config.registry.getUtility(IAuthenticationPolicy)
        def noprincipals(context, permission):
            return []
        pol.principals_allowed_by_permission = noprincipals
        context = testing.DummyModel()
        wrapper = DummyContentViewWrapper(context, None)
        inst = self._makeOne('view')
        result = inst(wrapper, None)
        self.assertEqual(result, [(NoWay, NoWay)])

    def test_it_unnamedpermission_no_permissions_registered(self):
        from ..discriminators import NoWay
        inst = self._makeOne()
        context = testing.DummyModel()
        wrapper = DummyContentViewWrapper(context, None)
        result = inst(wrapper, None)
        self.assertEqual(result, [(NoWay, NoWay)])

    def test_it_unnamedpermission_two_permissions_registered(self):
        self.config.add_permission('view')
        self.config.add_permission('edit')
        inst = self._makeOne()
        context = testing.DummyModel()
        wrapper = DummyContentViewWrapper(context, None)
        result = inst(wrapper, None)
        self.assertEqual(
            sorted(result),
            [('system.Everyone', 'edit'), ('system.Everyone', 'view')]
            )

class Test_get_name(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _callFUT(self, object, default):
        from ..discriminators import get_name
        return get_name(object, default)

    def test_it_has_no_name(self):
        context = object()
        wrapper = DummyContentViewWrapper(context, None)
        result = self._callFUT(wrapper, None)
        self.assertEqual(result, None)

    def test_it_has_name(self):
        context = testing.DummyModel()
        context.__name__ = 'foo'
        wrapper = DummyContentViewWrapper(context, None)
        result = self._callFUT(wrapper, None)
        self.assertEqual(result, 'foo')

class TestCatalogViewDiscriminator(unittest.TestCase):
    def _makeOne(self, name):
        from ..discriminators import CatalogViewDiscriminator
        return CatalogViewDiscriminator(name)

    def _makeWrapper(self, content, view_factory):
        return DummyContentViewWrapper(content, view_factory)

    def test_ctor(self):
        inst = self._makeOne('abc')
        self.assertEqual(inst.method_name, 'abc')

    def test_call_wrapper_is_True(self):
        inst = self._makeOne('attr')
        wrapper = DummyContentViewWrapper(None, True)
        result = inst(wrapper, None)
        self.assertEqual(result, None)

    def test_call_wrapper_has_attr(self):
        inst = self._makeOne('attr')
        content = object()
        factory = DummyViewFactory
        wrapper = self._makeWrapper(content, factory)
        result = inst(wrapper, None)
        self.assertEqual(result, 'attr')

    def test_call_wrapper_doesnt_have_attr(self):
        inst = self._makeOne('noattr')
        content = object()
        factory = DummyViewFactory
        wrapper = self._makeWrapper(content, factory)
        result = inst(wrapper, None)
        self.assertEqual(result, None)


class DummyViewFactory(object):
    def __init__(self, content):
        self.content = content

    def attr(self, default):
        return 'attr'

class DummyContentViewWrapper(object):
    def __init__(self, content, view_factory):
        self.content = content
        self.view_factory = view_factory

