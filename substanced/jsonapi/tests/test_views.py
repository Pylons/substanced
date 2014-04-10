import colander
import unittest

from decimal import Decimal
from pyramid import testing

from ...property import PropertySheet
from ...schema import Schema


class TestJsonApiExceptionView(unittest.TestCase):

    def _call_fut(self, context, request):
        from ..views import jsonapi_exception_view as fut
        return fut(context, request)

    def test_it(self):
        self.assertEqual(
            self._call_fut(Exception("Oh noes!"), testing.DummyRequest),
            {'error': 'Oh noes!'})


class TestContentPropertiesAPI(unittest.TestCase):

    def setUp(self):
        self.config = config = testing.setUp()
        config.include('substanced.content')
        config.add_content_type(
            "Dummy", DummyContent, propertysheets=(
                ('One', DummyPropertySheetOne),
                ('Two', DummyPropertySheetTwo)
            ))

    def _make_one(self, context, request):
        from ..views import ContentPropertiesAPI
        return ContentPropertiesAPI(context, request)

    def test_get(self):
        context = DummyContent(a='foo', b=42, c=Decimal('21.1'), d=False)
        request = testing.DummyRequest()
        view = self._make_one(context, request)
        self.assertEqual(view.get(), {
            'Two': {'c': '21.1', 'd': 'false'},
            'One': {'a': u'foo', 'b': '42'}})

    def test_has_permission_to(self):
        view = self._make_one(None, None)
        self.assertTrue(
            view._has_permission_to('joemama', DummyPropertySheetOne))

    def test_get_no_permission(self):
        self.config.testing_securitypolicy(permissive=False)
        context = DummyContent(a='foo', b=42, c=Decimal('21.1'), d=False)
        request = testing.DummyRequest()
        view = self._make_one(context, request)
        self.assertEqual(view.get(), {})

    def test_update(self):
        context = DummyContent(a='foo', b=42, c=Decimal('21.1'), d=False)
        request = testing.DummyRequest(json_body={
            'One': {'a': 'bar', 'b': '43'},
            'Two': {'c': '21.2', 'd': 'true'}
        })
        view = self._make_one(context, request)
        self.assertEqual(view.update().status_int, 204)
        self.assertEqual(context.a, 'bar')
        self.assertEqual(context.b, 43)
        self.assertEqual(context.c, Decimal('21.2'))
        self.assertEqual(context.d, True)

    def test_update_no_permission(self):
        from pyramid.httpexceptions import HTTPForbidden
        self.config.testing_securitypolicy(permissive=False)
        context = DummyContent(a='foo', b=42, c=Decimal('21.1'), d=False)
        request = testing.DummyRequest(json_body={
            'One': {'a': 'bar', 'b': '43'},
            'Two': {'c': '21.2', 'd': 'true'}
        })
        view = self._make_one(context, request)
        with self.assertRaises(HTTPForbidden):
            view.update()

    def test_delete(self):
        root = testing.DummyResource()
        root['foo'] = context = testing.DummyResource()
        request = testing.DummyRequest()
        view = self._make_one(context, request)
        self.assertEqual(view.delete().status_int, 204)
        self.assertTrue('foo' not in root)


class DummyContent(object):

    def __init__(self, **kw):
        self.__dict__.update(kw)


class DummySchemaOne(Schema):
    a = colander.SchemaNode(colander.String())
    b = colander.SchemaNode(colander.Int())


class DummySchemaTwo(Schema):
    c = colander.SchemaNode(colander.Decimal())
    d = colander.SchemaNode(colander.Boolean())


class DummyPropertySheetOne(PropertySheet):
    schema = DummySchemaOne()


class DummyPropertySheetTwo(PropertySheet):
    schema = DummySchemaTwo()

