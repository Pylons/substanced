import sys
import unittest

from zope.interface import (
    Interface,
    taggedValue,
    directlyProvidedBy,
    implementer,
    )

class TestContentRegistry(unittest.TestCase):
    def _makeOne(self):
        from . import ContentRegistry
        return ContentRegistry()

    def test_add(self):
        inst = self._makeOne()
        inst.add('here', True)
        self.assertEqual(inst.factories['here'], True)
        self.assertEqual(inst.meta['here'], {})

    def test_add_with_meta(self):
        inst = self._makeOne()
        inst.add('foo', True, icon='fred')
        self.assertEqual(inst.factories['foo'], True)
        self.assertEqual(inst.meta['foo'], {'icon':'fred'})
        
    def test_create(self):
        inst = self._makeOne()
        inst.factories['dummy'] = lambda a: a
        self.assertEqual(inst.create('dummy', 'a'), 'a')

    def test_istype_true(self):
        inst = self._makeOne()
        dummy = Dummy()
        dummy.__content_type__ = 'dummy'
        self.assertTrue(inst.istype(dummy, 'dummy'))
        
    def test_istype_false(self):
        inst = self._makeOne()
        dummy = Dummy()
        dummy.__content_type__ = 'notdummy'
        self.assertFalse(inst.istype(dummy, 'dummy'))

    def test_typeof(self):
        inst = self._makeOne()
        dummy = Dummy()
        dummy.__content_type__ = 'dummy'
        self.assertEqual(inst.typeof(dummy), 'dummy')

    def test_typeof_ct_missing(self):
        inst = self._makeOne()
        dummy = Dummy()
        self.assertEqual(inst.typeof(dummy), None)

    def test_metadata(self):
        inst = self._makeOne()
        inst.factories['dummy'] = True
        inst.factories['category'] = True
        inst.meta['dummy'] = {'icon':'icon-name'}
        dummy = Dummy()
        dummy.__content_type__ = 'dummy'
        self.assertEqual(inst.metadata(dummy, 'icon'), 'icon-name')

    def test_metadata_notfound(self):
        inst = self._makeOne()
        inst.factories['dummy'] = True
        inst.factories['category'] = True
        inst.meta['dummy'] = {'icon':'icon-name'}
        dummy = Dummy()
        dummy.__content_type__ = 'dummy'
        self.assertEqual(inst.metadata(dummy, 'doesntexist'), None)

    def test_all(self):
        inst = self._makeOne()
        inst.factories['dummy'] = True
        inst.factories['category'] = True
        self.assertEqual(sorted(inst.all()), ['category', 'dummy'])
        
class Test_content(unittest.TestCase):
    def _makeOne(self, content_type):
        from ..content import content
        return content(content_type)

    def test_decorates_class(self):
        decorator = self._makeOne('special')
        venusian = DummyVenusian()
        decorator.venusian = venusian
        decorator.venusian.info.scope = 'class'
        class Dummy(object):
            pass
        wrapped = decorator(Dummy)
        self.assertTrue(wrapped is Dummy)
        config = call_venusian(venusian)
        ct = config.content_types
        self.assertEqual(len(ct), 1)

    def test_decorates_function(self):
        decorator = self._makeOne('special')
        venusian = DummyVenusian()
        decorator.venusian = venusian
        decorator.venusian.info.scope = 'class'
        def dummy(): pass
        wrapped = decorator(dummy)
        self.assertTrue(wrapped is dummy)
        config = call_venusian(venusian)
        ct = config.content_types
        self.assertEqual(len(ct), 1)

class Test_add_content_type(unittest.TestCase):
    def _callFUT(self, *arg, **kw):
        from . import add_content_type
        return add_content_type(*arg, **kw)

    def test_success_function(self):
        dummy = Dummy()
        def factory(): return dummy
        config = DummyConfig()
        config.registry.content = DummyContentRegistry()
        self._callFUT(config, 'foo', factory, category=ICategory)
        self.assertEqual(len(config.actions), 1)
        self.assertEqual(
            config.actions[0][0],
            (('sd-content-type', 'foo',),)
            )
        config.actions[0][1]['callable']()
        self.assertEqual(
            config.registry.content.added[0][1]['category'], ICategory)
        self.assertEqual(
            config.registry.content.added[0][0][0], 'foo')
        self.assertEqual(
            config.registry.content.added[0][0][1](), dummy)

    def test_success_class(self):
        config = DummyConfig()
        config.registry.content = DummyContentRegistry()
        class Foo(object):
            pass
        self._callFUT(config, 'foo', Foo, category=ICategory)
        self.assertEqual(len(config.actions), 1)
        self.assertEqual(
            config.actions[0][0],
            (('sd-content-type', 'foo',),)
            )
        config.actions[0][1]['callable']()
        self.assertEqual(
            config.registry.content.added[0][1]['category'], ICategory)
        self.assertEqual(
            config.registry.content.added[0][0][0], 'foo')
        content = config.registry.content.added[0][0][1]()
        self.assertEqual(content.__class__, Foo)

    def test_with_catalog_flag(self):
        from ..interfaces import IContent, ICatalogable
        config = DummyConfig()
        config.registry.content = DummyContentRegistry()
        class Foo(object):
            pass
        self._callFUT(config, 'foo', Foo, catalog=True)
        self.assertEqual(len(config.actions), 1)
        ifaces = config.actions[0][1]['introspectables'][0]['interfaces']
        self.assertEqual(ifaces, set((IContent, ICatalogable)))

    def test_with_propertysheets_flag(self):
        from ..interfaces import IContent, IPropertied
        config = DummyConfig()
        config.registry.content = DummyContentRegistry()
        class Foo(object):
            pass
        self._callFUT(config, 'foo', Foo, propertysheets=())
        self.assertEqual(len(config.actions), 1)
        ifaces = config.actions[0][1]['introspectables'][0]['interfaces']
        self.assertEqual(ifaces, set((IContent, IPropertied)))

    def test_content_type_is_interface(self):
        from ..interfaces import IContent
        config = DummyConfig()
        config.registry.content = DummyContentRegistry()
        class IFoo(Interface):
            pass
        class Foo(object):
            pass
        self._callFUT(config, IFoo, Foo)
        self.assertEqual(len(config.actions), 1)
        ifaces = config.actions[0][1]['introspectables'][0]['interfaces']
        self.assertEqual(ifaces, set((IContent, IFoo)))
        
    def test_factory_implements_interface(self):
        from ..interfaces import IContent
        config = DummyConfig()
        config.registry.content = DummyContentRegistry()
        class IFoo(Interface):
            pass
        @implementer(IFoo)
        class Foo(object):
            pass
        self._callFUT(config, 'foo', Foo)
        self.assertEqual(len(config.actions), 1)
        ifaces = config.actions[0][1]['introspectables'][0]['interfaces']
        self.assertEqual(ifaces, set((IContent, IFoo)))
        
class Test_provides_factory(unittest.TestCase):
    def _callFUT(self, factory, content_type, interfaces):
        from . import provides_factory
        return provides_factory(factory, content_type, interfaces)

    def test_content_factory_function_ct_already_assigned(self):
        class Foo(object):
            __content_type__ = 'dummy'
        newfactory = self._callFUT(Foo, 'notdummy', ())
        ob = newfactory()
        self.assertTrue(ob.__class__ is Foo)
        self.assertEqual(ob.__content_type__, 'notdummy')

    def test_content_factory_function_type(self):
        class Foo(object):
            pass
        newfactory = self._callFUT(Foo, 'dummy', ())
        ob = newfactory()
        self.assertTrue(ob.__class__ is Foo)
        self.assertEqual(ob.__content_type__, 'dummy')

    def test_content_factory_function_interfaces(self):
        class Foo(object):
            pass
        foo = Foo()
        def factory():
            return foo
        newfactory = self._callFUT(factory, 'dummy', (IDummy,))
        self.assertFalse(newfactory is factory)
        ob = newfactory()
        self.assertTrue(IDummy.providedBy(ob))
        self.assertTrue(IDummy in directlyProvidedBy(ob))

class DummyContentRegistry(object):
    def __init__(self):
        self.added = []

    def add(self, *arg, **meta):
        self.added.append((arg, meta))

class ICategory(Interface):
    pass

class IDummy(Interface):
    taggedValue('icon', 'icon-name')

class Dummy(object):
    pass

class DummyIntrospectable(dict):
    def __init__(self, *arg, **kw):
        pass

class DummyConfig(object):
    introspectable = DummyIntrospectable
    def __init__(self):
        self.registry = Dummy()
        self.actions = []
        self.content_types = []
    def action(self, *arg, **kw):
        self.actions.append((arg, kw))
    def with_package(self, module):
        return self
    def add_content_type(self, *arg, **kw):
        self.content_types.append((arg, kw))
        
class DummyVenusianContext(object):
    def __init__(self):
        self.config = DummyConfig()

def call_venusian(venusian, context=None):
    if context is None:
        context = DummyVenusianContext()
    for wrapped, callback, category in venusian.attachments:
        callback(context, None, None)
    return context.config
        
class DummyVenusianInfo(object):
    scope = 'notaclass'
    module = sys.modules['substanced.content.tests']
    codeinfo = 'codeinfo'

class DummyVenusian(object):
    def __init__(self, info=None):
        if info is None:
            info = DummyVenusianInfo()
        self.info = info
        self.attachments = []

    def attach(self, wrapped, callback, category=None):
        self.attachments.append((wrapped, callback, category))
        return self.info

