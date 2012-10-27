import unittest
from pyramid import testing

class TestPropertySheet(unittest.TestCase):
    def _makeOne(self, context, request):
        from . import PropertySheet
        return PropertySheet(context, request)

    def test_get(self):
        context = testing.DummyResource()
        request = testing.DummyRequest()
        inst = self._makeOne(context, request)
        context.title = 'title'
        context.description = 'description'
        vals = inst.get()
        self.assertEqual(vals['title'], 'title')
        self.assertEqual(vals['description'], 'description')

    def test_get_with_activateable(self):
        context = testing.DummyResource()
        L = []
        context._p_activate = lambda *arg: L.append(True)
        request = testing.DummyRequest()
        inst = self._makeOne(context, request)
        context.title = 'title'
        context.description = 'description'
        vals = inst.get()
        self.assertEqual(vals['title'], 'title')
        self.assertEqual(vals['description'], 'description')
        self.assertEqual(L, [True])

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



class DummyRegistry(object):
    def __init__(self):
        self.subscribed = []
    
    def subscribers(self, *args):
        self.subscribed.append(args)
        
