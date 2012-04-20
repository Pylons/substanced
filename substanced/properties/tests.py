import unittest
from pyramid import testing

class TestPropertiesView(unittest.TestCase):
    def _makeOne(self, request):
        from . import PropertiesView
        return PropertiesView(request)

    def test_ctor(self):
        request = testing.DummyRequest()
        resource = testing.DummyResource()
        resource.__propschema__ = True
        request.context = resource
        inst = self._makeOne(request)
        self.assertEqual(inst.schema, True)

    def test_save_success(self):
        request = testing.DummyRequest()
        request.flash_undo = lambda *arg: None
        request.mgmt_path = lambda *arg: '/mgmt'
        request.registry = DummyRegistry()
        resource = testing.DummyResource()
        resource.__propschema__ = True
        properties = []
        resource.set_properties = lambda *arg: properties.append(arg)
        request.context = resource
        inst = self._makeOne(request)
        response = inst.save_success({'a':1})
        self.assertEqual(response.location, '/mgmt')
        self.assertEqual(properties, [({'a': 1},)])
        self.assertTrue(request.registry.subscribed)

    def test_show(self):
        request = testing.DummyRequest()
        resource = testing.DummyResource()
        resource.__propschema__ = True
        resource.get_properties = lambda *arg: {'a':1}
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
        
        
