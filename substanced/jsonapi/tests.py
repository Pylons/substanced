import unittest
from pyramid import testing

class Test_add_jsonapi_view(unittest.TestCase):
    def _callFUT(self, config, **kw):
        from . import add_jsonapi_view
        return add_jsonapi_view(config, **kw)

    def _makeConfig(self):
        config = DummyConfigurator()
        return config

    def test_default_permission_is_view(self):
        config = self._makeConfig()
        self._callFUT(config)
        self.assertEqual(config._added['permission'], 'view')

    def test_default_route_name_is_substanced_api(self):
        config = self._makeConfig()
        self._callFUT(config)
        self.assertEqual(config._added['route_name'], 'substanced_api')

    def test_default_renderer_is_json(self):
        config = self._makeConfig()
        self._callFUT(config)
        self.assertEqual(config._added['renderer'], 'json')


class Test_jsonapi_view(unittest.TestCase):
    def setUp(self):
        testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _getTargetClass(self):
        from . import jsonapi_view
        return jsonapi_view

    def _makeOne(self, *arg, **kw):
        return self._getTargetClass()(*arg, **kw)
        
    def test_call_function(self):
        decorator = self._makeOne()
        venusian = DummyVenusian()
        decorator.venusian = venusian
        def foo(): pass
        wrapped = decorator(foo)
        self.assertTrue(wrapped is foo)
        context = testing.DummyResource()
        context.config = DummyConfigurator()
        venusian.callback(context, None, 'abc')
        self.assertEqual(context.config.view, 'abc')

    def test_call_class_no_attr(self):
        decorator = self._makeOne()
        info = DummyVenusianInfo(scope='class')
        venusian = DummyVenusian(info)
        decorator.venusian = venusian
        def foo(): pass
        wrapped = decorator(foo)
        self.assertTrue(wrapped is foo)
        context = testing.DummyResource()
        context.config = DummyConfigurator()
        venusian.callback(context, None, None)
        self.assertEqual(context.config.settings['attr'], 'foo')

    def test_call_class_with_attr(self):
        decorator = self._makeOne(attr='bar')
        info = DummyVenusianInfo(scope='class')
        venusian = DummyVenusian(info)
        decorator.venusian = venusian
        def foo(): pass
        wrapped = decorator(foo)
        self.assertTrue(wrapped is foo)
        context = testing.DummyResource()
        context.config = DummyConfigurator()
        venusian.callback(context, None, None)
        self.assertEqual(context.config.settings['attr'], 'bar')


class DummyVenusianInfo(object):
    scope = None
    codeinfo = None
    module = None
    def __init__(self, **kw):
        self.__dict__.update(kw)
    
class DummyVenusian(object):
    def __init__(self, info=None):
        if info is None:
            info = DummyVenusianInfo()
        self.info = info
        
    def attach(self, wrapped, callback, category):
        self.wrapped = wrapped
        self.callback = callback
        self.category = category
        return self.info


class DummyConfigurator(object):
    _ainfo = None
    def __init__(self):
        self._actions = []
        self._added = None
        
    def maybe_dotted(self, thing):
        return thing

    def add_view(self, **kw):
        self._added = kw

    def add_jsonapi_view(self, view=None, **settings):
        self.view = view
        self.settings = settings

    def with_package(self, other):
        return self
