import sys
import unittest

from zope.interface import (
    Interface,
    directlyProvides,
    alsoProvides,
    taggedValue,
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

class TestContentCategory(unittest.TestCase):
    def _makeOne(self, category_iface):
        from . import ContentCategory
        return ContentCategory(category_iface)

    def test_add(self):
        inst = self._makeOne(ICategory)
        inst.add(IDummy, True)
        self.assertEqual(inst.factories[IDummy], True)

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

    def test_provided_by_true(self):
        inst = self._makeOne(ICategory)
        dummy = Dummy()
        directlyProvides(dummy, ICategory)
        self.assertTrue(inst.provided_by(dummy))

    def test_provided_by_false(self):
        inst = self._makeOne(ICategory)
        dummy = Dummy()
        self.assertFalse(inst.provided_by(dummy))

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
        
class TestContentCategories(unittest.TestCase):
    def _makeOne(self):
        from . import ContentCategories
        return ContentCategories()

    def test_add_no_category(self):
        inst = self._makeOne()
        class IFoo(Interface):
            pass
        class Factory(object):
            pass
        inst.add(IFoo, Factory)
        self.assertEqual(inst.categories[IContent].factories[IFoo], Factory)
        self.assertTrue(IContent in IFoo.__iro__)
        self.assertTrue(IContent in IFoo.__bases__)
        
    def test_add_with_category(self):
        inst = self._makeOne()
        class IFoo(Interface):
            pass
        class Factory(object):
            pass
        inst.add(IFoo, Factory, category=ICategory)
        self.assertEqual(inst.categories[ICategory].factories[IFoo], Factory)
        self.assertTrue(ICategory in IFoo.__iro__)
        self.assertTrue(ICategory in IFoo.__bases__)

    def test___getitem__(self):
        inst = self._makeOne()
        inst.categories['a'] = 1
        self.assertEqual(inst['a'], 1)
        
    def test_create(self):
        inst = self._makeOne()
        category = DummyCategory('abc')
        inst.categories[IContent] = category
        self.assertEqual(inst.create(IDummy, 'a'), 'abc')
        self.assertEqual(category.content_iface, IDummy)
        self.assertEqual(category.arg, ('a',))

    def test_provided_by(self):
        inst = self._makeOne()
        dummy = Dummy()
        inst.categories[IContent] = DummyCategory(None)
        self.assertTrue(inst.provided_by(dummy))

    def test_first(self):
        inst = self._makeOne()
        inst.categories[IContent] = DummyCategory(None)
        dummy = Dummy()
        self.assertEqual(inst.first(dummy), None)
        
    def test_all_with_context(self):
        inst = self._makeOne()
        inst.categories[IContent] = DummyCategory(None)
        dummy = Dummy()
        self.assertEqual(inst.all(dummy), [])

    def test_all_no_context(self):
        inst = self._makeOne()
        inst.categories[IContent] = DummyCategory(None)
        self.assertEqual(inst.all(), [])
        
    def test_metadata(self):
        inst = self._makeOne()
        inst.categories[IContent] = DummyCategory(None)
        dummy = Dummy()
        self.assertEqual(inst.metadata(dummy, 'abc'), 'abc')

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

    def test_category_iface_not_IInterface(self):
        from pyramid.exceptions import ConfigurationError
        self.assertRaises(
            ConfigurationError,
            self._callFUT,
            None, IDummy, None, category=object())
        
    def test_success(self):
        def factory(): pass
        config = DummyConfig()
        config.registry.content = DummyContentCategories()
        class IFoo(Interface):
            pass
        self._callFUT(config, IFoo, factory, category=ICategory)
        self.assertEqual(len(config.actions), 1)
        self.assertEqual(
            config.actions[0][0],
            (('content-type', IFoo, ICategory,),)
            )
        config.actions[0][1]['callable']()
        self.assertEqual(
            config.registry.content.added,
            [((IFoo, factory), {'category':ICategory})])

class DummyContentCategories(object):
    def __init__(self):
        self.added = []

    def add(self, *arg, **meta):
        self.added.append((arg, meta))

class DummyCategory(object):
    def __init__(self, result):
        self.result = result

    def create(self, content_iface, *arg, **kw):
        self.content_iface = content_iface
        self.arg = arg
        self.kw = kw
        return self.result

    def provided_by(self, resource):
        return True

    def all(self, context=None):
        return []

    def first(self, context):
        return None

    def metadata(self, context, name, default=None):
        return name
        
class ICategory(Interface):
    pass

class IDummy(Interface):
    taggedValue('icon', 'icon-name')

class Dummy(object):
    pass

class DummyConfig(object):
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
