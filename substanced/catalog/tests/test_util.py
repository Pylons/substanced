import unittest
from pyramid import testing


class Test_assertint(unittest.TestCase):
    def _callFUT(self, oid):
        from ..util import assertint
        return assertint(oid)

    def test_it_int(self):
        self.assertEqual(self._callFUT(1), None)

    def test_it_long(self):
        self.assertEqual(self._callFUT(1L), None)

    def test_it_nonit(self):
        self.assertRaises(ValueError, self._callFUT, None)

class Test_oid_from_resource(unittest.TestCase):
    def _callFUT(self, resource, oid):
        from ..util import oid_from_resource
        return oid_from_resource(resource, oid)

    def test_it_oid_not_None_oid_not_int(self):
        self.assertRaises(ValueError, self._callFUT, None, 'abc')

    def test_it_oid_not_None_oid_int(self):
        self.assertEqual(self._callFUT(None, 1), 1)
        
    def test_it_oid_None_resource_has_no_oid(self):
        self.assertRaises(ValueError, self._callFUT, None, None)

    def test_it_oid_None_resource_has_oid(self):
        resource = testing.DummyResource()
        resource.__oid__ = 1
        self.assertEqual(self._callFUT(resource, None), 1)

class Test_oid_from_resource_or_oid(unittest.TestCase):
    def _callFUT(self, resource_or_oid):
        from ..util import oid_from_resource_or_oid
        return oid_from_resource_or_oid(resource_or_oid)

    def test_is_not_resource_oid_is_not_int(self):
        self.assertRaises(ValueError, self._callFUT, None)

    def test_is_not_resource_oid_is_int(self):
        self.assertEqual(self._callFUT(1), 1)

    def test_is_resource_with_oid(self):
        resource = testing.DummyResource()
        resource.__oid__ = 1
        self.assertEqual(self._callFUT(resource), 1)
