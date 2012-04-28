import unittest
from pyramid import testing

class TestPropertiesView(unittest.TestCase):
    def _makeOne(self, request):
        from . import PropertySheetsView
        return PropertySheetsView(request)

    def test_ctor_no_subpath(self):
        request = testing.DummyRequest()
        resource = testing.DummyResource()
        resource.__propsheets__ = [('name', DummyPropertySheet)]
        request.context = resource
        inst = self._makeOne(request)
        self.assertEqual(inst.active_sheet_name, 'name')
        self.assertTrue(inst.schema, 'schema')
        self.assertEqual(inst.sheet_names, ['name'])

    def test_ctor_with_subpath(self):
        request = testing.DummyRequest()
        request.subpath = ('othername',)
        resource = testing.DummyResource()
        resource.__propsheets__ = [('othername', DummyPropertySheet)]
        request.context = resource
        inst = self._makeOne(request)
        self.assertEqual(inst.active_sheet_name, 'othername')
        self.assertTrue(inst.schema, 'schema')
        self.assertEqual(inst.sheet_names, ['othername'])

    def test_save_success(self):
        request = testing.DummyRequest()
        request.mgmt_path = lambda *arg: '/mgmt'
        resource = testing.DummyResource()
        resource.__propsheets__ = [('name', DummyPropertySheet)]
        request.context = resource
        inst = self._makeOne(request)
        response = inst.save_success({'a':1})
        self.assertEqual(response.location, '/mgmt')
        self.assertEqual(inst.active_sheet.struct, {'a': 1})
        self.assertTrue(inst.active_sheet.after)

    def test_show(self):
        request = testing.DummyRequest()
        resource = testing.DummyResource()
        resource.__propsheets__ = [('name', DummyPropertySheet)]
        request.context = resource
        inst = self._makeOne(request)
        form = DummyForm()
        result = inst.show(form)
        self.assertTrue(form.rendered)
        self.assertEqual(result['form'], None)

class TestPropertySheet(unittest.TestCase):
    def _makeOne(self, context, request):
        from . import PropertySheet
        return PropertySheet(context, request)

    def test_get_schema(self):
        context = testing.DummyResource()
        request = testing.DummyRequest()
        inst = self._makeOne(context, request)
        schema = DummySchema()
        inst.schema = schema
        self.assertEqual(inst.get_schema(), schema)
        self.assertEqual(schema.bound, {'request':request})
        
    def test_get(self):
        context = testing.DummyResource()
        request = testing.DummyRequest()
        inst = self._makeOne(context, request)
        context.title = 'title'
        context.description = 'description'
        vals = inst.get()
        self.assertEqual(vals['title'], 'title')
        self.assertEqual(vals['description'], 'description')

    def test_set(self):
        context = testing.DummyResource()
        request = testing.DummyRequest()
        inst = self._makeOne(context, request)
        context.title = 'title'
        context.description = 'description'
        inst.set(dict(title='t', description='d'))
        self.assertEqual(context.title, 't')
        self.assertEqual(context.description, 'd')

    def test_after_set(self):
        request = testing.DummyRequest()
        request.registry = DummyRegistry()
        def flash_undo(msg, category):
            self.assertEqual(msg, 'Updated properties')
            self.assertEqual(category, 'success')
            context.flashed = True
        request.flash_undo = flash_undo
        context = testing.DummyResource()
        inst = self._makeOne(context, request)
        inst.after_set()
        self.assertTrue(request.registry.subscribed)
        self.assertTrue(context.flashed)

class DummyRegistry(object):
    def __init__(self):
        self.subscribed = []
    
    def subscribers(self, *args):
        self.subscribed.append(args)
        
class DummyForm(object):
    def __init__(self):
        self.rendered = []
        
    def render(self, appstruct=None, readonly=False):
        self.rendered.append((appstruct, readonly))

class DummySchema(object):
    def bind(self, **kw):
        self.bound = kw
        return self
        
class DummyPropertySheet(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def get(self):
        return {}

    def set(self, struct):
        self.struct = struct

    def after_set(self):
        self.after = True

    def get_schema(self):
        return 'schema'
