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

    def tearDown(self):
        testing.tearDown()

    def _getTargetClass(self):
        from . import Folder
        return Folder

    def _makeOne(self, data=None, family=None):
        klass = self._getTargetClass()
        return klass(data, family=family)

    def test_klass_provides_IFolder(self):
        klass = self._getTargetClass()
        from ..interfaces import IFolder
        verifyClass(IFolder, klass)

    def test_inst_provides_IFolder(self):
        from ..interfaces import IFolder
        inst = self._makeOne()
        verifyObject(IFolder, inst)

    def test_ctor_alternate_family(self):
        import BTrees
        inst = self._makeOne(family=BTrees.family32)
        self.assertEqual(inst.family, BTrees.family32)

    def _registerEventListener(self, listener, iface):
        self.config.registry.registerHandler(
            listener, (iface, Interface, Interface))

    def test_keys(self):
        folder = self._makeOne({'a': 1, 'b': 2})
        self.assertEqual(list(folder.keys()), ['a', 'b'])

    def test_keys_with_order(self):
        folder = self._makeOne({'a': 1, 'b': 2})
        folder.order = ['b', 'a']
        self.assertEqual(list(folder.keys()), ['b', 'a'])

    def test_keys_after_del_order(self):
        folder = self._makeOne({'a': 1, 'b': 2})
        folder.order = ['b', 'a']
        del folder.order
        self.assertEqual(list(folder.keys()), ['a', 'b'])

    def test__iter__(self):
        folder = self._makeOne({'a': 1, 'b': 2})
        self.assertEqual(list(folder), ['a', 'b'])

    def test__iter___with_order(self):
        folder = self._makeOne({'a': 1, 'b': 2})
        folder.order = ['b', 'a']
        self.assertEqual(list(folder), ['b', 'a'])

    def test_values(self):
        folder = self._makeOne({'a': 1, 'b': 2})
        self.assertEqual(list(folder.values()), [1, 2])

    def test_values_with_order(self):
        folder = self._makeOne({'a': 1, 'b': 2})
        folder.order = ['b', 'a']
        self.assertEqual(list(folder.values()), [2, 1])

    def test_items(self):
        folder = self._makeOne({'a': 1, 'b': 2})
        self.assertEqual(list(folder.items()), [('a', 1), ('b', 2)])

    def test_items_with_order(self):
        folder = self._makeOne({'a': 1, 'b': 2})
        folder.order = ['b', 'a']
        self.assertEqual(list(folder.items()), [('b', 2), ('a', 1)])

    def test__len__(self):
        folder = self._makeOne({'a': 1, 'b': 2})
        self.assertEqual(len(folder), 2)
        del folder['a']
        self.assertEqual(len(folder), 1)

    def test__contains__(self):
        folder = self._makeOne({'a': 1, 'b': 2})
        self.failUnless('a' in folder)
        self.failIf('c' in folder)

    def test___nonzero__(self):
        folder = self._makeOne()
        self.failUnless(folder)

    def test___setitem__nonstring(self):
        folder = self._makeOne()
        self.assertRaises(ValueError, folder.__setitem__, None, None)

    def test___setitem__8bitstring(self):
        folder = self._makeOne()
        self.assertRaises(ValueError, folder.__setitem__, '\xff', None)

    def test___setitem__empty(self):
        folder = self._makeOne()
        self.assertRaises(ValueError, folder.__setitem__, '', None)

    def test___setitem__(self):
        from ..interfaces import IObjectEvent
        from ..interfaces import IObjectWillBeAdded
        from ..interfaces import IObjectAdded
        events = []
        def listener(event, obj, container):
            events.append(event)
        self._registerEventListener(listener, IObjectEvent)
        dummy = DummyModel()
        folder = self._makeOne()
        self.assertEqual(folder._num_objects(), 0)
        folder['a'] = dummy
        self.assertEqual(folder._num_objects(), 1)
        self.assertEqual(len(events), 2)
        self.failUnless(IObjectWillBeAdded.providedBy(events[0]))
        self.assertEqual(events[0].object, dummy)
        self.assertEqual(events[0].parent, folder)
        self.assertEqual(events[0].name, 'a')
        self.failUnless(IObjectAdded.providedBy(events[1]))
        self.assertEqual(events[1].object, dummy)
        self.assertEqual(events[1].parent, folder)
        self.assertEqual(events[1].name, 'a')
        self.assertEqual(folder['a'], dummy)

    def test_add_name_wrongtype(self):
        folder = self._makeOne()
        self.assertRaises(ValueError, folder.add, 1, 'foo')

    def test_add_name_empty(self):
        folder = self._makeOne()
        self.assertRaises(ValueError, folder.add, '', 'foo')

    def test_add_reserved_name(self):
        folder = self._makeOne()
        self.assertRaises(ValueError, folder.add, 'foo', None,
                          reserved_names=('foo',))

    def test_add_with_slash_in_name(self):
        folder = self._makeOne()
        self.assertRaises(ValueError, folder.add, '/abc', None)

    def test_add_begins_with_atat(self):
        folder = self._makeOne()
        self.assertRaises(ValueError, folder.add, '@@abc', None)

    def test_check_name(self):
        folder = self._makeOne()
        self.assertRaises(ValueError, folder.check_name, '@@abc')

    def test_add_send_events(self):
        from ..interfaces import IObjectEvent
        from ..interfaces import IObjectWillBeAdded
        from ..interfaces import IObjectAdded
        events = []
        def listener(event, obj, container):
            events.append(event)
        self._registerEventListener(listener, IObjectEvent)
        dummy = DummyModel()
        folder = self._makeOne()
        self.assertEqual(folder._num_objects(), 0)
        folder.add('a', dummy, send_events=True)
        self.assertEqual(folder._num_objects(), 1)
        self.assertEqual(len(events), 2)
        self.failUnless(IObjectWillBeAdded.providedBy(events[0]))
        self.assertEqual(events[0].object, dummy)
        self.assertEqual(events[0].parent, folder)
        self.assertEqual(events[0].name, 'a')
        self.failUnless(IObjectAdded.providedBy(events[1]))
        self.assertEqual(events[1].object, dummy)
        self.assertEqual(events[1].parent, folder)
        self.assertEqual(events[1].name, 'a')
        self.assertEqual(folder['a'], dummy)

    def test_add_suppress_events(self):
        from ..interfaces import IObjectEvent
        events = []
        def listener(event, obj, container):
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
        from ..exceptions import FolderKeyError
        dummy = DummyModel()
        folder = self._makeOne({'a': dummy})
        self.assertEqual(folder._num_objects(), 1)
        self.assertRaises(FolderKeyError, folder.__setitem__, 'a', dummy)
        self.assertEqual(folder._num_objects(), 1)

    def test___delitem__(self):
        from ..interfaces import IObjectEvent
        from ..interfaces import IObjectRemoved
        from ..interfaces import IObjectWillBeRemoved
        events = []
        def listener(event, obj, container):
            events.append(event)
        self._registerEventListener(listener, IObjectEvent)
        dummy = DummyModel()
        dummy.__parent__ = None
        dummy.__name__ = None
        folder = self._makeOne({'a': dummy})
        self.assertEqual(folder._num_objects(), 1)
        del folder['a']
        self.assertEqual(folder._num_objects(), 0)
        self.assertEqual(len(events), 2)
        self.failUnless(IObjectWillBeRemoved.providedBy(events[0]))
        self.failUnless(IObjectRemoved.providedBy(events[1]))
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
        folder = self._makeOne({'a': dummy})
        self.assertTrue(folder.remove("a") is dummy)

    def test_remove_send_events(self):
        from ..interfaces import IObjectEvent
        from ..interfaces import IObjectRemoved
        from ..interfaces import IObjectWillBeRemoved
        events = []
        def listener(event, obj, container):
            events.append(event)
        self._registerEventListener(listener, IObjectEvent)
        dummy = DummyModel()
        dummy.__parent__ = None
        dummy.__name__ = None
        folder = self._makeOne({'a': dummy})
        self.assertEqual(folder._num_objects(), 1)
        folder.remove('a', send_events=True)
        self.assertEqual(folder._num_objects(), 0)
        self.assertEqual(len(events), 2)
        self.failUnless(IObjectWillBeRemoved.providedBy(events[0]))
        self.failUnless(IObjectRemoved.providedBy(events[1]))
        self.assertEqual(events[0].object, dummy)
        self.assertEqual(events[0].parent, folder)
        self.assertEqual(events[0].name, 'a')
        self.assertFalse(events[0].moving)
        self.assertEqual(events[1].object, dummy)
        self.assertEqual(events[1].parent, folder)
        self.assertEqual(events[1].name, 'a')
        self.assertFalse(events[1].moving)

        self.failIf(hasattr(dummy, '__parent__'))
        self.failIf(hasattr(dummy, '__name__'))

    def test_remove_suppress_events(self):
        from ..interfaces import IObjectEvent
        events = []
        def listener(event, obj, container):
            events.append(event) #pragma NO COVER
        self._registerEventListener(listener, IObjectEvent)
        dummy = DummyModel()
        dummy.__parent__ = None
        dummy.__name__ = None
        folder = self._makeOne({'a': dummy})
        self.assertEqual(folder._num_objects(), 1)
        folder.remove('a', send_events=False)
        self.assertEqual(folder._num_objects(), 0)
        self.assertEqual(len(events), 0)
        self.failIf(hasattr(dummy, '__parent__'))
        self.failIf(hasattr(dummy, '__name__'))

    def test_remove_moving(self):
        from ..interfaces import IObjectEvent
        from ..interfaces import IObjectRemoved
        from ..interfaces import IObjectWillBeRemoved
        events = []
        def listener(event, obj, container):
            events.append(event) #pragma NO COVER
        self._registerEventListener(listener, IObjectEvent)
        dummy = DummyModel()
        dummy.__parent__ = None
        dummy.__name__ = None
        folder = self._makeOne({'a': dummy})
        self.assertEqual(folder._num_objects(), 1)
        folder.remove('a', moving=True)
        self.assertEqual(folder._num_objects(), 0)
        self.failIf(hasattr(dummy, '__parent__'))
        self.failIf(hasattr(dummy, '__name__'))
        self.assertEqual(len(events), 2)
        self.failUnless(IObjectWillBeRemoved.providedBy(events[0]))
        self.failUnless(IObjectRemoved.providedBy(events[1]))
        self.assertEqual(events[0].object, dummy)
        self.assertEqual(events[0].parent, folder)
        self.assertEqual(events[0].name, 'a')
        self.assertTrue(events[0].moving)
        self.assertEqual(events[1].object, dummy)
        self.assertEqual(events[1].parent, folder)
        self.assertEqual(events[1].name, 'a')
        self.assertTrue(events[1].moving)

    def test_move_no_newname(self):
        folder = self._makeOne()
        other = self._makeOne()
        model = DummyModel()
        folder['a'] = model
        folder.move('a', other)
        self.assertEqual(other['a'], model)
        self.assertEqual(other['a'].__name__, 'a')
        self.assertEqual(other['a'].__parent__, other)
        self.assertFalse('a' in folder)

    def test_move_newname(self):
        folder = self._makeOne()
        other = self._makeOne()
        model = DummyModel()
        folder['a'] = model
        folder.move('a', other, 'b')
        self.assertEqual(other['b'], model)
        self.assertEqual(other['b'].__name__, 'b')
        self.assertEqual(other['b'].__parent__, other)
        self.assertFalse('a' in other)
        self.assertFalse('a' in folder)

    def test_move_is_service(self):
        folder = self._makeOne()
        folder.__services__ = ('a',)
        other = self._makeOne()
        model = DummyModel()
        folder['a'] = model
        folder.move('a', other)
        self.assertEqual(other['a'], model)
        self.assertEqual(other.__services__, ('a',))

    def test_copy_no_newname(self):
        folder = self._makeOne()
        other = self._makeOne()
        model = DummyExportableModel()
        folder['a'] = model
        folder.copy('a', other)
        self.assertEqual(other['a'].__name__, 'a')
        self.assertEqual(other['a'].__parent__, other)
        self.assertTrue('a' in folder)

    def test_copy_newname(self):
        folder = self._makeOne()
        other = self._makeOne()
        model = DummyExportableModel()
        folder['a'] = model
        folder.copy('a', other, 'b')
        self.assertEqual(other['b'].__name__, 'b')
        self.assertEqual(other['b'].__parent__, other)
        self.assertFalse('a' in other)
        self.assertTrue('a' in folder)

    def test_rename(self):
        folder = self._makeOne()
        model = DummyModel()
        folder['a'] = model
        folder.rename('a', 'b')
        self.assertEqual(folder['b'], model)
        self.assertEqual(folder['b'].__name__, 'b')
        self.assertEqual(folder['b'].__parent__, folder)
        self.assertFalse('a' in folder)

    def test_remove_with_order_removes_name(self):
        folder = self._makeOne()
        folder['a'] = DummyModel()
        folder['b'] = DummyModel()
        folder.order = ['a', 'b']
        folder.remove('a')
        self.assertEqual(folder.order, ['b'])

    def test_replace_existing(self):
        folder = self._makeOne()
        other = self._makeOne()
        model = DummyModel()
        folder['a'] = model
        folder.replace('a', other)
        self.assertEqual(folder['a'], other)
        self.assertEqual(other.__name__, 'a')
        self.assertEqual(other.__parent__, folder)

    def test_replace_nonexisting(self):
        folder = self._makeOne()
        other = self._makeOne()
        folder.replace('a', other)
        self.assertEqual(folder['a'], other)
        self.assertEqual(other.__name__, 'a')
        self.assertEqual(other.__parent__, folder)

    def test_pop_success(self):
        from ..interfaces import IObjectEvent
        from ..interfaces import IObjectRemoved
        from ..interfaces import IObjectWillBeRemoved
        dummy = DummyModel()
        dummy.__parent__ = None
        dummy.__name__ = None
        events = []
        def listener(event, obj, container):
            events.append(event)
        self._registerEventListener(listener, IObjectEvent)
        folder = self._makeOne({'a': dummy})
        result = folder.pop('a')
        self.assertEqual(result, dummy)
        self.assertEqual(folder._num_objects(), 0)
        self.assertEqual(len(events), 2)
        self.failUnless(IObjectWillBeRemoved.providedBy(events[0]))
        self.failUnless(IObjectRemoved.providedBy(events[1]))
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
        self.assertRaises(ValueError,
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

    def test_find_service_missing(self):
        inst = self._makeOne()
        self.assertEqual(inst.find_service('abc'), None)

    def test_find_service_found(self):
        inst = self._makeOne()
        inst2 = self._makeOne()
        inst.add('inst2', inst2)
        inst.__services__ = ('inst2,')
        self.assertEqual(inst.find_service('inst2'), inst2)

    def test_find_services_missing(self):
        inst = self._makeOne()
        self.assertEqual(inst.find_services('abc'), [])

    def test_find_services_found(self):
        inst = self._makeOne()
        inst2 = self._makeOne()
        inst.add('inst2', inst2)
        inst.__services__ = ('inst2,')
        self.assertEqual(inst.find_services('inst2'), [inst2])

    def test_add_service(self):
        inst = self._makeOne()
        foo = testing.DummyResource()
        inst.add_service('foo', foo)
        self.assertEqual(inst['foo'], foo)
        self.assertEqual(inst.__services__, ('foo',))

    def test_add_service_withregistry(self):
        inst = self._makeOne()
        foo = testing.DummyResource()
        inst.add_service('foo', foo, registry=self.config.registry)
        self.assertEqual(inst['foo'], foo)
        self.assertEqual(inst.__services__, ('foo',))

    def test__notify_no_registry(self):
        def f(t, n):
            self.assertEqual(t, (event, event.object, inst))
            self.assertEqual(n, None)
        self.config.registry.subscribers = f
        inst = self._makeOne()
        event = DummyModel()
        event.object = DummyModel()
        inst._notify(event)

class TestSequentialAutoNamingFolder(unittest.TestCase):
    def _makeOne(self, d=None, autoname_length=None, autoname_start=None):
        from . import SequentialAutoNamingFolder
        return SequentialAutoNamingFolder(
            d,
            autoname_length=autoname_length,
            autoname_start=autoname_start
            )

    def test_next_name_empty(self):
        inst = self._makeOne()
        self.assertEqual(inst.next_name(None), '0'.zfill(7))

    def test_next_name_nonempty(self):
        ob = DummyModel()
        inst = self._makeOne({'000000000':ob})
        self.assertEqual(inst.next_name(None), '1'.zfill(7))

    def test_next_name_alternate_autoname_length(self):
        inst = self._makeOne(autoname_length=5)
        self.assertEqual(inst.next_name(None), '0'.zfill(5))

    def test_next_name_alternate_autoname_start(self):
        inst = self._makeOne(autoname_start=0)
        self.assertEqual(inst.next_name(None), '1'.zfill(7))

    def test_add_not_intifiable(self):
        ob = DummyModel()
        inst = self._makeOne()
        self.assertRaises(ValueError, inst.add, 'abcdef', ob)

    def test_add_intifiable(self):
        ob = DummyModel()
        inst = self._makeOne()
        inst.add('1', ob)
        self.assertTrue('1'.zfill(7) in inst)

    def test_add_next(self):
        ob = DummyModel()
        inst = self._makeOne()
        result = inst.add_next(ob)
        name = '0'.zfill(7)
        self.assertEqual(ob.__name__, name)
        self.assertTrue(name in inst)
        self.assertEqual(name, result)

class TestRandomAutoNamingFolder(unittest.TestCase):
    def _makeOne(self, d=None, autoname_length=None):
        from . import RandomAutoNamingFolder
        return RandomAutoNamingFolder(d, autoname_length=autoname_length)

    def test_next_name_doesntexist(self):
        inst = self._makeOne()
        inst._randomchoice = lambda *arg: 'x'
        self.assertEqual(inst.next_name(None), 'x' * 7)

    def test_next_name_exists(self):
        inst = self._makeOne()
        L = ['x'] * 7
        L.extend(['y'] * 7)
        def choice(vals):
            v = L.pop()
            return v
        inst._randomchoice = choice
        self.assertEqual(inst.next_name(None), 'y' * 7)

    def test_next_name_alternate_length(self):
        inst = self._makeOne(autoname_length=5)
        self.assertEqual(len(inst.next_name(None)), 5)
        
    def test_add_next(self):
        ob = DummyModel()
        inst = self._makeOne()
        result = inst.add_next(ob)
        self.assertEqual(ob.__name__, result)
        self.assertTrue(result in inst)
        self.assertEqual(len(result), 7)

class DummyModel(object):
    pass

class DummyExportImport(object):
    def __init__(self, obj):
        self.obj = obj

    def exportFile(self, oid, f):
        pass

    def importFile(self, f):
        import copy
        new_obj = copy.deepcopy(self.obj)
        new_obj.__objectid__ = 0
        return new_obj

class DummyExportableModel(object):
    _p_oid = 0

    @property
    def _p_jar(self):
        return DummyExportImport(self)

