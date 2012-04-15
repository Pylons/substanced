import sys
import unittest

from zope.interface import (
    Interface,
    alsoProvides,
    taggedValue,
    directlyProvidedBy,
    implementer,
    )

from ..interfaces import IContent

class IFoo(Interface):
    pass

class IBar(IFoo):
    pass

class Test_addbase(unittest.TestCase):
    def tearDown(self):
        # prevent whining from tests when unsubscribe happens
        IBar.__bases__ = (IFoo,)
        
    def _callFUT(self, I1, I2):
        from . import addbase
        return addbase(I1, I2)

    def test_already_in_iro(self):
        result = self._callFUT(IBar, IFoo)
        self.assertEqual(result, False)
        
    def test_not_in_iro(self):
        result = self._callFUT(IBar, IContent)
        self.assertEqual(result, True)
        self.failUnless(IContent in IBar.__bases__)
        self.failUnless(IContent in IBar.__iro__)

class TestContentRegistry(unittest.TestCase):
    def _makeOne(self, category_iface):
        from . import ContentRegistry
        return ContentRegistry(category_iface)

    def test_add(self):
        class IHere(Interface):
            pass
        inst = self._makeOne(ICategory)
        inst.add(IHere, True)
        self.assertEqual(inst.factories[IHere], True)
        self.assertTrue(ICategory in IHere.__iro__)
        self.assertTrue(ICategory in IHere.__bases__)

    def test_add_with_meta(self):
        inst = self._makeOne(ICategory)
        class IFoo(Interface):
            pass
        inst.add(IFoo, True, icon='fred')
        self.assertEqual(inst.factories[IFoo], True)
        self.assertEqual(IFoo.getTaggedValue('icon'), 'fred')
        
    def test_create(self):
        inst = self._makeOne(ICategory)
        inst.factories[IDummy] = lambda a: a
        self.assertEqual(inst.create(IDummy, 'a'), 'a')

    def test_all_no_context(self):
        inst = self._makeOne(ICategory)
        inst.factories[IDummy] = True
        self.assertEqual(inst.all(), [IDummy])

    def test_all_with_context(self):
        inst = self._makeOne(ICategory)
        inst.factories[IDummy] = True
        inst.factories[ICategory] = True
        dummy = Dummy()
        alsoProvides(dummy, IDummy)
        alsoProvides(dummy, ICategory)
        self.assertEqual(inst.all(dummy), [IDummy, ICategory])

    def test_all_with_context_noprovides(self):
        inst = self._makeOne(ICategory)
        inst.factories[IDummy] = True
        dummy = Dummy()
        self.assertEqual(inst.all(dummy), [])

    def test_all_with_meta_matching(self):
        class IFoo(Interface):
            pass
        IFoo.setTaggedValue('a', 1)
        inst = self._makeOne(ICategory)
        inst.factories[IFoo] = True
        self.assertEqual(inst.all(a=1), [IFoo])

    def test_all_with_meta_not_matching(self):
        class IFoo(Interface):
            pass
        IFoo.setTaggedValue('a', 1)
        inst = self._makeOne(ICategory)
        inst.factories[IFoo] = True
        self.assertEqual(inst.all(a=2), [])

    def test_all_with_meta_not_matching_missing(self):
        class IFoo(Interface):
            pass
        inst = self._makeOne(ICategory)
        inst.factories[IFoo] = True
        self.assertEqual(inst.all(a=2), [])
        
    def test_first(self):
        inst = self._makeOne(ICategory)
        inst.factories[IDummy] = True
        inst.factories[ICategory] = True
        dummy = Dummy()
        alsoProvides(dummy, IDummy)
        alsoProvides(dummy, ICategory)
        self.assertEqual(inst.first(dummy), IDummy)

    def test_first_noprovides(self):
        inst = self._makeOne(ICategory)
        inst.factories[IDummy] = True
        dummy = Dummy()
        self.assertRaises(ValueError, inst.first, dummy)

    def test_metadata(self):
        inst = self._makeOne(ICategory)
        inst.factories[IDummy] = True
        inst.factories[ICategory] = True
        dummy = Dummy()
        alsoProvides(dummy, IDummy)
        alsoProvides(dummy, ICategory)
        self.assertEqual(inst.metadata(dummy, 'icon'), 'icon-name')

    def test_metadata_notfound(self):
        inst = self._makeOne(ICategory)
        inst.factories[IDummy] = True
        inst.factories[ICategory] = True
        dummy = Dummy()
        alsoProvides(dummy, IDummy)
        alsoProvides(dummy, ICategory)
        self.assertEqual(inst.metadata(dummy, 'doesntexist'), None)
        
class Test_content(unittest.TestCase):
    def _makeOne(self, iface):
        from ..content import content
        return content(iface)

    def test_decorates_class(self):
        decorator = self._makeOne(ISpecial)
        venusian = DummyVenusian()
        decorator.venusian = venusian
        decorator.venusian.info.scope = 'class'
        wrapped = decorator(Special)
        self.assertTrue(wrapped is Special)
        self.assertTrue(ISpecial.implementedBy(Special))
        config = call_venusian(venusian)
        ct = config.content_types
        self.assertEqual(len(ct), 1)

    def test_decorates_function(self):
        decorator = self._makeOne(ISpecial)
        venusian = DummyVenusian()
        decorator.venusian = venusian
        decorator.venusian.info.scope = 'class'
        wrapped = decorator(special)
        self.assertTrue(wrapped is special)
        self.assertTrue(ISpecial.implementedBy(special))
        config = call_venusian(venusian)
        ct = config.content_types
        self.assertEqual(len(ct), 1)
        
class Test_add_content_type(unittest.TestCase):
    def _callFUT(self, *arg, **kw):
        from . import add_content_type
        return add_content_type(*arg, **kw)

    def test_content_iface_not_IInterface(self):
        from pyramid.exceptions import ConfigurationError
        self.assertRaises(
            ConfigurationError,
            self._callFUT,
            None, object(), None, category=IDummy)

    def test_success_function(self):
        dummy = Dummy()
        def factory(): return dummy
        config = DummyConfig()
        config.registry.content = DummyContentRegistry()
        class IFoo(Interface):
            pass
        self._callFUT(config, IFoo, factory, category=ICategory)
        self.assertEqual(len(config.actions), 1)
        self.assertEqual(
            config.actions[0][0],
            (('sd-content-type', IFoo,),)
            )
        config.actions[0][1]['callable']()
        self.assertEqual(
            config.registry.content.added[0][1]['category'], ICategory)
        self.assertEqual(
            config.registry.content.added[0][0][0], IFoo)
        self.assertEqual(
            config.registry.content.added[0][0][1](), dummy)
        self.assertTrue(IFoo.providedBy(dummy))

    def test_success_class(self):
        config = DummyConfig()
        config.registry.content = DummyContentRegistry()
        class Foo(object):
            pass
        class IFoo(Interface):
            pass
        self._callFUT(config, IFoo, Foo, category=ICategory)
        self.assertEqual(len(config.actions), 1)
        self.assertEqual(
            config.actions[0][0],
            (('sd-content-type', IFoo,),)
            )
        config.actions[0][1]['callable']()
        self.assertEqual(
            config.registry.content.added[0][1]['category'], ICategory)
        self.assertEqual(
            config.registry.content.added[0][0][0], IFoo)
        content = config.registry.content.added[0][0][1]()
        self.assertEqual(content.__class__, Foo)
        self.assertTrue(IFoo.providedBy(content))
        
class Test_provides_factory(unittest.TestCase):
    def _callFUT(self, factory, content_iface):
        from . import provides_factory
        return provides_factory(factory, content_iface)

    def test_content_already_provides(self):
        @implementer(IDummy)
        class Foo(object):
            pass
        foo = Foo()
        def factory():
            return foo
        newfactory = self._callFUT(factory, IDummy)
        self.assertFalse(newfactory is factory)
        ob = newfactory()
        self.assertTrue(IDummy.providedBy(ob))
        self.assertFalse(IDummy in directlyProvidedBy(ob))

    def test_content_provides_added(self):
        class Foo(object):
            pass
        foo = Foo()
        def factory():
            return foo
        newfactory = self._callFUT(factory, IDummy)
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

# use these special objects only in "content" decorator tests; the decorator
# uses "implementer", which mutates them.

class ISpecial(Interface): pass

class Special(object): pass

def special(): pass
