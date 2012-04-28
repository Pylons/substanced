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

    def test_save_success(self):
        request = testing.DummyRequest()
        request.flash_undo = lambda *arg: None
        request.mgmt_path = lambda *arg: '/mgmt'
        request.registry = DummyRegistry()
        resource = testing.DummyResource()
        resource.__propsheets__ = [('name', DummyPropertySheet)]
        request.context = resource
        inst = self._makeOne(request)
        response = inst.save_success({'a':1})
        self.assertEqual(response.location, '/mgmt')
        self.assertEqual(inst.active_sheet.struct, {'a': 1})
        self.assertTrue(request.registry.subscribed)

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

class DummyRegistry(object):
    def __init__(self):
        self.subscribed = []
    
    def subscribers(self, *args):
        self.subscribed.append(args)
        
class DummyForm(object):
    def __init__(self):
        self.rendered = []
        
    def render(self, appstruct):
        self.rendered.append(appstruct)
        
        
class DummyPropertySheet(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def get(self):
        return {}

    def set(self, struct):
        self.struct = struct

    def get_schema(self):
        return 'schema'
