import unittest
from pyramid import testing
import colander

class TestSchema(unittest.TestCase):
    def _getTargetClass(self):
        from . import Schema
        return Schema

    def _makeOne(self):
        return self._getTargetClass()()

    def test_validate_failure(self):
        from colander import Invalid
        inst = self._makeOne()
        request = DummyRequest()
        inst2 = inst.bind(request=request)
        self.assertRaises(Invalid, inst2.deserialize, {'_csrf_token_':'wrong'})

    def test_validate_missing(self):
        from colander import Invalid
        inst = self._makeOne()
        request = DummyRequest()
        inst2 = inst.bind(request=request)
        self.assertRaises(Invalid, inst2.deserialize, {})

    def test_validate_success(self):
        inst = self._makeOne()
        request = DummyRequest()
        inst2 = inst.bind(request=request)
        self.assertEqual(inst2.deserialize({'_csrf_token_':'csrf_token'}),{})

class TestRemoveCSRFMapping(unittest.TestCase):
    def _makeOne(self):
        from . import RemoveCSRFMapping
        return RemoveCSRFMapping()

    def test_deserialize_colander_null(self):
        inst = self._makeOne()
        node = object()
        result = inst.deserialize(node, colander.null)
        self.assertEqual(result, colander.null)

    def test_deserialize_real_mapping(self):
        inst = self._makeOne()
        node = colander.SchemaNode(colander.Mapping())
        a = colander.SchemaNode(colander.String(), name='a')
        node.add(a)
        result = inst.deserialize(node, {'_csrf_token_':'token', 'a':'1'})
        self.assertEqual(result, {'a':'1'})
        
class DummySession(dict):
    def get_csrf_token(self):
        return 'csrf_token'

class DummyRequest(testing.DummyRequest):
    def __init__(self, *arg, **kw):
        testing.DummyRequest.__init__(self, *arg, **kw)
        self.session = DummySession()
    
