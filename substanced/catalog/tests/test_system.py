import unittest
from pyramid import testing

from zope.interface import Interface
from zope.interface import alsoProvides

class TestSystemIndexViews(unittest.TestCase):
    def _makeOne(self, resource):
        from ..system import SystemIndexViews
        return SystemIndexViews(resource)

    def test_interfaces(self):
        resource = testing.DummyResource()
        class Dummy1(Interface):
            pass
        class Dummy2(Interface):
            pass
        alsoProvides(resource, Dummy1)
        alsoProvides(resource, Dummy2)
        inst = self._makeOne(resource)
        result = inst.interfaces(None)
        self.assertEqual(len(result), 3)
        self.assertTrue(Dummy1 in result)
        self.assertTrue(Dummy2 in result)
        self.assertTrue(Interface in result)

    def test_containment(self):
        class Dummy1(Interface):
            pass
        class Dummy2(Interface):
            pass
        root = testing.DummyModel()
        alsoProvides(root, Dummy1)
        resource = testing.DummyResource()
        alsoProvides(resource, Dummy2)
        root['foo'] = resource
        inst = self._makeOne(resource)
        result = inst.containment(None)
        self.assertEqual(len(result), 3)
        self.assertTrue(Dummy1 in result)
        self.assertTrue(Dummy2 in result)
        self.assertTrue(Interface in result)

    def test_name_has_no_name(self):
        resource = object()
        inst = self._makeOne(resource)
        result = inst.name(None)
        self.assertEqual(result, None)

    def test_name_has_name(self):
        resource = testing.DummyResource()
        resource.__name__ = 'foo'
        inst = self._makeOne(resource)
        result = inst.name(None)
        self.assertEqual(result, 'foo')

    def test_name_has_name_None(self):
        resource = testing.DummyResource()
        resource.__name__ = None
        inst = self._makeOne(resource)
        result = inst.name('abc')
        self.assertEqual(result, 'abc')
