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

