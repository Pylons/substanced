import datetime
import unittest
from pyramid import testing

from zope.interface import Interface
from zope.interface import alsoProvides

class TestGetTextRepr(unittest.TestCase):
    def setUp(self):
        testing.cleanUp()

    def tearDown(self):
        testing.tearDown()

    def _callFUT(self, object, default):
        from ..discriminators import get_textrepr
        return get_textrepr(object, default)

    def test_one_element(self):
        context = testing.DummyModel()
        context.texts = ('title',)
        textrepr = self._callFUT(context, None)
        self.assertEqual(textrepr, 'title')

    def test_two_elements(self):
        context = testing.DummyModel()
        context.texts = ('title', 'description')
        textrepr = self._callFUT(context, None)
        self.assertEqual(textrepr, 'title ' * 10 + 'description')

    def test_two_elements_first_empty(self):
        context = testing.DummyModel()
        context.texts = ('', 'description')
        textrepr = self._callFUT(context, None)
        self.assertEqual(textrepr, 'description')
        
    def test_None(self):
        context = testing.DummyModel()
        context.texts = None
        textrepr = self._callFUT(context, None)
        self.assertEqual(textrepr, None)

    def test_string(self):
        context = testing.DummyModel()
        context.texts = 'title'
        textrepr = self._callFUT(context, None)
        self.assertEqual(textrepr, 'title')

    def test_callable(self):
        context = testing.DummyModel()
        context.texts = lambda: 'title'
        textrepr = self._callFUT(context, None)
        self.assertEqual(textrepr, 'title')
        
class _TestGetDate(object):

    def test_not_set(self):
        context = testing.DummyModel()
        result = self._callFUT(context, None)
        self.assertEqual(result, None)

    def test_w_datetime(self):
        from ...util import coarse_datetime_repr
        context = testing.DummyModel()
        now = datetime.datetime.now()
        self._decorate(context, now)
        result = self._callFUT(context, None)
        self.assertEqual(result, coarse_datetime_repr(now))

    def test_w_date(self):
        from ...util import coarse_datetime_repr
        context = testing.DummyModel()
        today = datetime.date.today()
        self._decorate(context, today)
        result = self._callFUT(context, None)
        self.assertEqual(result, coarse_datetime_repr(today))

    def test_w_invalid_value(self):
        context = testing.DummyModel()
        self._decorate(context, 'notadatetime')
        result = self._callFUT(context, None)
        self.assertEqual(result, None)

class TestGetCreationDate(unittest.TestCase, _TestGetDate):
    def _callFUT(self, object, default):
        from ..discriminators import get_creation_date
        return get_creation_date(object, default)

    def _decorate(self, context, val):
        context.created = val

class TestGetModifiedDate(unittest.TestCase, _TestGetDate):
    def _callFUT(self, object, default):
        from ..discriminators import get_modified_date
        return get_modified_date(object, default)

    def _decorate(self, context, val):
        context.modified = val

class TestGetInterfaces(unittest.TestCase):
    def _callFUT(self, object, default):
        from ..discriminators import get_interfaces
        return get_interfaces(object, default)

    def test_it(self):
        context = testing.DummyModel()
        class Dummy1(Interface):
            pass
        class Dummy2(Interface):
            pass
        alsoProvides(context, Dummy1)
        alsoProvides(context, Dummy2)
        result = self._callFUT(context, None)
        self.assertEqual(len(result), 4)
        self.assertTrue(Dummy1 in result)
        self.assertTrue(Dummy2 in result)
        self.assertTrue(Interface in result)
        self.assertTrue(testing.DummyModel in result)

class TestGetContainment(unittest.TestCase):
    def test_it(self):
        from ..discriminators import get_containment
        class Dummy1(Interface):
            pass
        class Dummy2(Interface):
            pass
        root = testing.DummyModel()
        alsoProvides(root, Dummy1)
        context = testing.DummyModel()
        alsoProvides(context, Dummy2)
        root['foo'] = context
        result = get_containment(context, None)
        self.assertEqual(len(result), 4)
        self.assertTrue(Dummy1 in result)
        self.assertTrue(Dummy2 in result)
        self.assertTrue(Interface in result)
        self.assertTrue(testing.DummyModel in result) 

class TestGetTitle(unittest.TestCase):
    def _callFUT(self, object, default):
        from ..discriminators import get_title
        return get_title(object, default)

    def test_it(self):
        context = testing.DummyModel()
        result = self._callFUT(context, None)
        self.assertEqual(result, '')
        context.title = 'foo'
        result = self._callFUT(context, None)
        self.assertEqual(result, 'foo')

    def test_lowercase(self):
        context = testing.DummyModel()
        result = self._callFUT(context, None)
        self.assertEqual(result, '')
        context.title = 'FoobaR'
        result = self._callFUT(context, None)
        self.assertEqual(result, 'foobar')

class TestGetAllowedToView(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
        
    def _callFUT(self, object, default):
        from ..discriminators import get_allowed_to_view
        return get_allowed_to_view(object, default)

    def test_it(self):
        context = testing.DummyModel()
        result = self._callFUT(context, None)
        self.assertEqual(result, ['system.Everyone'])

    def test_it_notpermitted(self):
        from pyramid.interfaces import IAuthenticationPolicy
        self.config.testing_securitypolicy(permissive=False)
        from ..discriminators import NoWay
        pol = self.config.registry.getUtility(IAuthenticationPolicy)
        def noprincipals(context, permission):
            return []
        pol.principals_allowed_by_permission = noprincipals
        context = testing.DummyModel()
        result = self._callFUT(context, None)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].__class__, NoWay)

class Test_get_name(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _callFUT(self, object, default):
        from ..discriminators import get_name
        return get_name(object, default)

    def test_it_has_no_name(self):
        context = object()
        result = self._callFUT(context, None)
        self.assertEqual(result, None)

    def test_it_has_name(self):
        context = testing.DummyModel()
        context.__name__ = 'foo'
        result = self._callFUT(context, None)
        self.assertEqual(result, 'foo')

class TestContentViewDiscriminator(unittest.TestCase):
    def _makeOne(self, name, fallback=None):
        from ..discriminators import ContentViewDiscriminator
        return ContentViewDiscriminator(name, fallback=fallback)

    def _makeWrapper(self, content, view_factory=None):
        return DummyContentViewWrapper(content, view_factory)

    def _fallback(self, obj, default):
        return obj

    def test_ctor_both_None(self):
        self.assertRaises(ValueError, self._makeOne, None, None)

    def test_ctor_name_None(self):
        inst = self._makeOne(None, 'abc')
        self.assertEqual(inst.name, None)
        self.assertEqual(inst.fallback, 'abc')

    def test_ctor_fallback_not_provided(self):
        inst = self._makeOne('abc')
        self.assertEqual(inst.name, 'abc')
        self.assertEqual(inst.fallback, None)

    def test_call_name_is_None(self):
        inst = self._makeOne(None, self._fallback)
        content = object()
        wrapper = self._makeWrapper(content)
        result = inst(wrapper, None)
        self.assertEqual(result, content)

    def test_call_name_is_not_None_wrapper_has_attr(self):
        inst = self._makeOne('attr', self._fallback)
        content = object()
        factory = DummyViewFactory
        wrapper = self._makeWrapper(content, factory)
        result = inst(wrapper, None)
        self.assertEqual(result, 'attr')

    def test_call_name_is_not_None_wrapper_doesnt_have_attr(self):
        inst = self._makeOne('noattr', self._fallback)
        content = object()
        factory = DummyViewFactory
        wrapper = self._makeWrapper(content, factory)
        result = inst(wrapper, None)
        self.assertEqual(result, content)

class DummyViewFactory(object):
    def __init__(self, content):
        self.content = content

    def attr(self):
        return 'attr'

class DummyContentViewWrapper(object):
    def __init__(self, content, view_factory):
        self.content = content
        self.view_factory = view_factory

