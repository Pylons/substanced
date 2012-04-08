import unittest
from pyramid import testing

from zope.interface import Interface
from zope.interface.verify import (
    verifyObject,
    verifyClass
    )

class TestFolder(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def _getTargetClass(self):
        from . import Folder
        return Folder

    def _makeOne(self, data=None):
        klass = self._getTargetClass()
        return klass(data)

    def test_klass_provides_IFolder(self):
        klass = self._getTargetClass()
        from ..interfaces import IFolder
        verifyClass(IFolder, klass)
        
    def test_inst_provides_IFolder(self):
        from ..interfaces import IFolder
        inst = self._makeOne()
        verifyObject(IFolder, inst)

    def _registerEventListener(self, listener, iface):
        self.config.registry.registerHandler(listener, (Interface, iface))

    def test_keys(self):
        folder = self._makeOne({'a':1, 'b':2})
        self.assertEqual(list(folder.keys()), ['a', 'b'])

    def test_keys_with_order(self):
        folder = self._makeOne({'a':1, 'b':2})
        folder.order = ['b', 'a']
        self.assertEqual(list(folder.keys()), ['b', 'a'])

    def test_keys_after_del_order(self):
        folder = self._makeOne({'a':1, 'b':2})
        folder.order = ['b', 'a']
        del folder.order
        self.assertEqual(list(folder.keys()), ['a', 'b'])

    def test__iter__(self):
        folder = self._makeOne({'a':1, 'b':2})
        self.assertEqual(list(folder), ['a', 'b'])

    def test__iter___with_order(self):
        folder = self._makeOne({'a':1, 'b':2})
        folder.order = ['b', 'a']
        self.assertEqual(list(folder), ['b', 'a'])

    def test_values(self):
        folder = self._makeOne({'a':1, 'b':2})
        self.assertEqual(list(folder.values()), [1, 2])

    def test_values_with_order(self):
        folder = self._makeOne({'a':1, 'b':2})
        folder.order = ['b', 'a']
        self.assertEqual(list(folder.values()), [2, 1])

    def test_items(self):
        folder = self._makeOne({'a':1, 'b':2})
        self.assertEqual(list(folder.items()), [('a', 1), ('b', 2)])

    def test_items_with_order(self):
        folder = self._makeOne({'a':1, 'b':2})
        folder.order = ['b', 'a']
        self.assertEqual(list(folder.items()), [('b', 2), ('a', 1)])

    def test__len__(self):
        folder = self._makeOne({'a':1, 'b':2})
        self.assertEqual(len(folder), 2)
        del folder['a']
        self.assertEqual(len(folder), 1)

    def test__contains__(self):
        folder = self._makeOne({'a':1, 'b':2})
        self.failUnless('a' in folder)
        self.failIf('c' in folder)

    def test___nonzero__(self):
        folder = self._makeOne()
        self.failUnless(folder)

    def test___setitem__nonstring(self):
        folder = self._makeOne()
        self.assertRaises(TypeError, folder.__setitem__, None, None)
        
    def test___setitem__8bitstring(self):
        folder = self._makeOne()
        self.assertRaises(UnicodeDecodeError, folder.__setitem__, '\xff', None)

    def test___setitem__empty(self):
        folder = self._makeOne()
        self.assertRaises(TypeError, folder.__setitem__, '', None)

    def test___setitem__(self):
        from ..interfaces import IObjectEvent
        from ..interfaces import IObjectWillBeAddedEvent
        from ..interfaces import IObjectAddedEvent
        events = []
        def listener(object, event):
            events.append(event)
        self._registerEventListener(listener, IObjectEvent)
        dummy = DummyModel()
        folder = self._makeOne()
        self.assertEqual(folder._num_objects(), 0)
        folder['a'] = dummy
        self.assertEqual(folder._num_objects(), 1)
        self.assertEqual(len(events), 2)
        self.failUnless(IObjectWillBeAddedEvent.providedBy(events[0]))
        self.assertEqual(events[0].object, dummy)
        self.assertEqual(events[0].parent, folder)
        self.assertEqual(events[0].name, 'a')
        self.failUnless(IObjectAddedEvent.providedBy(events[1]))
        self.assertEqual(events[1].object, dummy)
        self.assertEqual(events[1].parent, folder)
        self.assertEqual(events[1].name, 'a')
        self.assertEqual(folder['a'], dummy)

    def test_add_name_wrongtype(self):
        folder = self._makeOne()
        self.assertRaises(TypeError, folder.add, 1, 'foo')

    def test_add_name_empty(self):
        folder = self._makeOne()
        self.assertRaises(TypeError, folder.add, '', 'foo')

    def test_add_dont_allow_services(self):
        folder = self._makeOne()
        self.assertRaises(KeyError, folder.add, '__services__', None)

    def test_add_send_events(self):
        from ..interfaces import IObjectEvent
        from ..interfaces import IObjectWillBeAddedEvent
        from ..interfaces import IObjectAddedEvent
        events = []
        def listener(object, event):
            events.append(event)
        self._registerEventListener(listener, IObjectEvent)
        dummy = DummyModel()
        folder = self._makeOne()
        self.assertEqual(folder._num_objects(), 0)
        folder.add('a', dummy, send_events=True)
        self.assertEqual(folder._num_objects(), 1)
        self.assertEqual(len(events), 2)
        self.failUnless(IObjectWillBeAddedEvent.providedBy(events[0]))
        self.assertEqual(events[0].object, dummy)
        self.assertEqual(events[0].parent, folder)
        self.assertEqual(events[0].name, 'a')
        self.failUnless(IObjectAddedEvent.providedBy(events[1]))
        self.assertEqual(events[1].object, dummy)
        self.assertEqual(events[1].parent, folder)
        self.assertEqual(events[1].name, 'a')
        self.assertEqual(folder['a'], dummy)

    def test_add_suppress_events(self):
        from ..interfaces import IObjectEvent
        events = []
        def listener(object, event):
            events.append(event) #pragma NO COVER
        self._registerEventListener(listener, IObjectEvent)
        dummy = DummyModel()
        folder = self._makeOne()
        self.assertEqual(folder._num_objects(), 0)
        folder.add('a', dummy, send_events=False)
        self.assertEqual(folder._num_objects(), 1)
        self.assertEqual(len(events), 0)
        self.assertEqual(folder['a'], dummy)

    def test_add_with_order_appends_name(self):
        folder = self._makeOne()
        folder.order = []
        folder.add('a', DummyModel())
        self.assertEqual(folder.order, ['a'])
        folder.add('b', DummyModel())
        self.assertEqual(folder.order, ['a', 'b'])

    def test___setitem__exists(self):
        dummy = DummyModel()
        folder = self._makeOne({'a':dummy})
        self.assertEqual(folder._num_objects(), 1)
        self.assertRaises(KeyError, folder.__setitem__, 'a', dummy)
        self.assertEqual(folder._num_objects(), 1)

    def test___delitem__(self):
        from ..interfaces import IObjectEvent
        from ..interfaces import IObjectRemovedEvent
        from ..interfaces import IObjectWillBeRemovedEvent
        events = []
        def listener(object, event):
            events.append(event)
        self._registerEventListener(listener, IObjectEvent)
        dummy = DummyModel()
        dummy.__parent__ = None
        dummy.__name__ = None
        folder = self._makeOne({'a':dummy})
        self.assertEqual(folder._num_objects(), 1)
        del folder['a']
        self.assertEqual(folder._num_objects(), 0)
        self.assertEqual(len(events), 2)
        self.failUnless(IObjectWillBeRemovedEvent.providedBy(events[0]))
        self.failUnless(IObjectRemovedEvent.providedBy(events[1]))
        self.assertEqual(events[0].object, dummy)
        self.assertEqual(events[0].parent, folder)
        self.assertEqual(events[0].name, 'a')
        self.assertEqual(events[1].object, dummy)
        self.assertEqual(events[1].parent, folder)
        self.assertEqual(events[1].name, 'a')
        self.failIf(hasattr(dummy, '__parent__'))
        self.failIf(hasattr(dummy, '__name__'))

    def test_remove_miss(self):
        folder = self._makeOne()
        self.assertRaises(KeyError, folder.remove, "nonesuch")

    def test_remove_returns_object(self):
        dummy = DummyModel()
        dummy.__parent__ = None
        dummy.__name__ = None
        folder = self._makeOne({'a':dummy})
        self.assertTrue(folder.remove("a") is dummy)

    def test_remove_send_events(self):
        from ..interfaces import IObjectEvent
        from ..interfaces import IObjectRemovedEvent
        from ..interfaces import IObjectWillBeRemovedEvent
        events = []
        def listener(object, event):
            events.append(event)
        self._registerEventListener(listener, IObjectEvent)
        dummy = DummyModel()
        dummy.__parent__ = None
        dummy.__name__ = None
        folder = self._makeOne({'a':dummy})
        self.assertEqual(folder._num_objects(), 1)
        folder.remove('a', send_events=True)
        self.assertEqual(folder._num_objects(), 0)
        self.assertEqual(len(events), 2)
        self.failUnless(IObjectWillBeRemovedEvent.providedBy(events[0]))
        self.failUnless(IObjectRemovedEvent.providedBy(events[1]))
        self.assertEqual(events[0].object, dummy)
        self.assertEqual(events[0].parent, folder)
        self.assertEqual(events[0].name, 'a')
        self.assertEqual(events[1].object, dummy)
        self.assertEqual(events[1].parent, folder)
        self.assertEqual(events[1].name, 'a')
        self.failIf(hasattr(dummy, '__parent__'))
        self.failIf(hasattr(dummy, '__name__'))

    def test_remove_suppress_events(self):
        from ..interfaces import IObjectEvent
        events = []
        def listener(object, event):
            events.append(event) #pragma NO COVER
        self._registerEventListener(listener, IObjectEvent)
        dummy = DummyModel()
        dummy.__parent__ = None
        dummy.__name__ = None
        folder = self._makeOne({'a':dummy})
        self.assertEqual(folder._num_objects(), 1)
        folder.remove('a', send_events=False)
        self.assertEqual(folder._num_objects(), 0)
        self.assertEqual(len(events), 0)
        self.failIf(hasattr(dummy, '__parent__'))
        self.failIf(hasattr(dummy, '__name__'))

    def test_remove_with_order_removes_name(self):
        folder = self._makeOne()
        folder['a'] = DummyModel()
        folder['b'] = DummyModel()
        folder.order = ['a', 'b']
        folder.remove('a')
        self.assertEqual(folder.order, ['b'])

    def test_pop_success(self):
        from ..interfaces import IObjectEvent
        from ..interfaces import IObjectRemovedEvent
        from ..interfaces import IObjectWillBeRemovedEvent
        dummy = DummyModel()
        dummy.__parent__ = None
        dummy.__name__ = None
        events = []
        def listener(object, event):
            events.append(event)
        self._registerEventListener(listener, IObjectEvent)
        folder = self._makeOne({'a':dummy})
        result = folder.pop('a')
        self.assertEqual(result, dummy)
        self.assertEqual(folder._num_objects(), 0)
        self.assertEqual(len(events), 2)
        self.failUnless(IObjectWillBeRemovedEvent.providedBy(events[0]))
        self.failUnless(IObjectRemovedEvent.providedBy(events[1]))
        self.assertEqual(events[0].object, dummy)
        self.assertEqual(events[0].parent, folder)
        self.assertEqual(events[0].name, 'a')
        self.assertEqual(events[1].object, dummy)
        self.assertEqual(events[1].parent, folder)
        self.assertEqual(events[1].name, 'a')
        self.failIf(hasattr(dummy, '__parent__'))
        self.failIf(hasattr(dummy, '__name__'))

    def test_pop_fail_nodefault(self):
        folder = self._makeOne()
        self.assertRaises(KeyError, folder.pop, 'nonesuch')

    def test_pop_fail_withdefault(self):
        folder = self._makeOne()
        result = folder.pop('a', 123)
        self.assertEqual(result, 123)

    def test_repr(self):
        folder = self._makeOne()
        folder.__name__ = 'thefolder'
        r = repr(folder)
        self.assertTrue(
            r.startswith("<substanced.folder.Folder object 'thefolder"))
        self.assertTrue(r.endswith('>'))

    def test_str(self):
        folder = self._makeOne()
        folder.__name__ = 'thefolder'
        r = str(folder)
        self.assertTrue(
            r.startswith("<substanced.folder.Folder object 'thefolder"))
        self.assertTrue(r.endswith('>'))

    def test_unresolveable_unicode_setitem(self):
        name = unicode('La Pe\xc3\xb1a', 'utf-8').encode('latin-1')
        folder = self._makeOne()
        self.assertRaises(UnicodeDecodeError, 
                          folder.__setitem__, name, DummyModel())

    def test_resolveable_unicode_setitem(self):
        name = 'La'
        folder = self._makeOne()
        folder[name] = DummyModel()
        self.failUnless(folder.get(name))

    def test_unresolveable_unicode_getitem(self):
        name = unicode('La Pe\xc3\xb1a', 'utf-8').encode('latin-1')
        folder = self._makeOne()
        self.assertRaises(UnicodeDecodeError, folder.__getitem__, name)

    def test_resolveable_unicode_getitem(self):
        name = 'La'
        folder = self._makeOne()
        folder[name] = DummyModel()
        self.failUnless(folder[name])

class DummyModel:
    pass

