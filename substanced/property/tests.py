import unittest
from pyramid import testing

class TestPropertySheetsView(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
        
    def _makeOne(self, request):
        from . import PropertySheetsView
        return PropertySheetsView(request)

    def test_ctor_no_viewable_sheet_factories(self):
        from pyramid.httpexceptions import HTTPNotFound
        request = testing.DummyRequest()
        request.registry = testing.DummyResource()
        request.registry.content = DummyContent([])
        resource = testing.DummyResource()
        request.context = resource
        self.assertRaises(HTTPNotFound, self._makeOne, request)

    def test_ctor_no_subpath(self):
        request = testing.DummyRequest()
        request.registry = testing.DummyResource()
        request.registry.content = DummyContent([('name', DummyPropertySheet)])
        resource = testing.DummyResource()
        request.context = resource
        inst = self._makeOne(request)
        self.assertEqual(inst.active_sheet_name, 'name')
        self.assertTrue(inst.schema, 'schema')
        self.assertEqual(inst.sheet_names, ['name'])

    def test_ctor_with_subpath(self):
        request = testing.DummyRequest()
        request.subpath = ('othername',)
        request.registry = testing.DummyResource()
        request.registry.content = DummyContent(
            [('othername', DummyPropertySheet)])
        resource = testing.DummyResource()
        request.context = resource
        inst = self._makeOne(request)
        self.assertEqual(inst.active_sheet_name, 'othername')
        self.assertTrue(inst.schema, 'schema')
        self.assertEqual(inst.sheet_names, ['othername'])

    def test_save_success(self):
        request = testing.DummyRequest()
        request.mgmt_path = lambda *arg: '/mgmt'
        request.registry = testing.DummyResource()
        request.registry.content = DummyContent(
            [('name', DummyPropertySheet)])
        resource = testing.DummyResource()
        request.context = resource
        inst = self._makeOne(request)
        response = inst.save_success({'a':1})
        self.assertEqual(response.location, '/mgmt')
        self.assertEqual(inst.active_sheet.struct, {'a': 1})
        self.assertTrue(inst.active_sheet.after)

    def test_save_success_no_change_permission(self):
        from pyramid.httpexceptions import HTTPForbidden
        request = testing.DummyRequest()
        request.mgmt_path = lambda *arg: '/mgmt'
        sheet_factory = testing.DummyResource()
        sheet_factory.__call__ = lambda *arg: sheet_factory
        sheet_factory.get_schema = lambda *arg: None
        sheet_factory.permissions = [('change', 'sdi.change')]
        request.registry.content = DummyContent(
            [('name', sheet_factory)])
        resource = testing.DummyResource()
        request.context = resource
        inst = self._makeOne(request)
        self.config.testing_securitypolicy(permissive=False)
        self.assertRaises(HTTPForbidden, inst.save_success, {'a':1})

    def test_show(self):
        request = testing.DummyRequest()
        request.registry = testing.DummyResource()
        request.registry.content = DummyContent(
            [('name', DummyPropertySheet)])
        resource = testing.DummyResource()
        request.context = resource
        inst = self._makeOne(request)
        form = DummyForm()
        result = inst.show(form)
        self.assertTrue(form.rendered)
        self.assertEqual(result['form'], None)

    def test_has_permission_to_no_permissions(self):
        request = testing.DummyRequest()
        request.registry = testing.DummyResource()
        request.registry.content = DummyContent(
            [('name', DummyPropertySheet)])
        resource = testing.DummyResource()
        request.context = resource
        inst = self._makeOne(request)
        result = inst.has_permission_to('view', DummyPropertySheet)
        self.assertTrue(result)

    def test_has_permission_to_no_specific_permission(self):
        request = testing.DummyRequest()
        request.registry = testing.DummyResource()
        sheet_factory = testing.DummyResource()
        sheet_factory.__call__ = lambda *arg: sheet_factory
        sheet_factory.get_schema = lambda *arg: None
        sheet_factory.permissions = [('edit', 'sdi.edit')]
        request.registry.content = DummyContent(
            [('name', sheet_factory)])
        resource = testing.DummyResource()
        request.context = resource
        inst = self._makeOne(request)
        result = inst.has_permission_to('view', DummyPropertySheet)
        self.assertTrue(result)
        
    def test_has_permission_to_denied(self):
        request = testing.DummyRequest()
        request.registry = self.config.registry
        sheet_factory = testing.DummyResource()
        sheet_factory.__call__ = lambda *arg: sheet_factory
        sheet_factory.get_schema = lambda *arg: None
        sheet_factory.permissions = [('view', 'sdi.view')]
        request.registry.content = DummyContent(
            [('name', sheet_factory)])
        resource = testing.DummyResource()
        request.context = resource
        inst = self._makeOne(request)
        self.config.testing_securitypolicy(permissive=False)
        result = inst.has_permission_to('view', sheet_factory)
        self.assertFalse(result)

    def test_viewable_sheet_factories_no_permission(self):
        sheet_factory = testing.DummyResource()
        sheet_factory.__call__ = lambda *arg: sheet_factory
        sheet_factory.get_schema = lambda *arg: None
        sheet_factory.permissions = [('view', 'sdi.view')]
        request = testing.DummyRequest()
        request.registry.content = DummyContent(
            [('name', sheet_factory)])
        resource = testing.DummyResource()
        request.context = resource
        inst = self._makeOne(request)
        self.config.testing_securitypolicy(permissive=False)
        result = inst.viewable_sheet_factories()
        self.assertEqual(result, [])
        

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
        self.assertEqual(schema.bound, {'request':request, 'context':context})
        
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
        def flash_with_undo(msg, category):
            self.assertEqual(msg, 'Updated properties')
            self.assertEqual(category, 'success')
            context.flashed = True
        request.flash_with_undo = flash_with_undo
        context = testing.DummyResource()
        inst = self._makeOne(context, request)
        inst.after_set()
        self.assertTrue(request.registry.subscribed)
        self.assertTrue(context.flashed)

class Test_has_permission_to_view_any_propertysheet(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _callFUT(self, context, request):
        from . import has_permission_to_view_any_propertysheet
        return has_permission_to_view_any_propertysheet(context, request)
        
    def test_no_candidates(self):
        request = testing.DummyRequest()
        request.registry.content = DummyContent([])
        context = testing.DummyResource()
        self.assertFalse(self._callFUT(context, request))
        
    def test_no_permission_required(self):
        request = testing.DummyRequest()
        request.registry.content = DummyContent([(True, True)])
        context = testing.DummyResource()
        self.assertTrue(self._callFUT(context, request))

    def test_permission_required_denied(self):
        self.config.testing_securitypolicy(permissive=False)
        request = testing.DummyRequest()
        sheet_factory = testing.DummyResource()
        sheet_factory.permissions = [('view', 'sdi.view')]
        request.registry.content = DummyContent([('sheet', sheet_factory)])
        context = testing.DummyResource()
        self.assertFalse(self._callFUT(context, request))

    def test_permission_required_allowed(self):
        self.config.testing_securitypolicy(permissive=True)
        request = testing.DummyRequest()
        sheet_factory = testing.DummyResource()
        sheet_factory.permissions = [('view', 'sdi.view')]
        request.registry.content = DummyContent([('sheet', sheet_factory)])
        context = testing.DummyResource()
        self.assertTrue(self._callFUT(context, request))

    def test_no_view_permission_required_allowed(self):
        request = testing.DummyRequest()
        sheet_factory = testing.DummyResource()
        sheet_factory.permissions = [('edit', 'sdi.edit')]
        request.registry.content = DummyContent([('sheet', sheet_factory)])
        context = testing.DummyResource()
        self.assertTrue(self._callFUT(context, request))

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

class DummyContent(object):
    def __init__(self, result):
        self.result = result

    def metadata(self, context, name, default=None):
        return self.result
    
