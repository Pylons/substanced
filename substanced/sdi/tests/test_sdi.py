import unittest
from pyramid import testing

class Test_add_mgmt_view(unittest.TestCase):
    def _callFUT(self, config, **kw):
        from .. import add_mgmt_view
        return add_mgmt_view(config, **kw)

    def _makeConfig(self):
        config = DummyConfigurator()
        return config

    def test_with_request_method(self):
        config = self._makeConfig()
        self._callFUT(config, request_method=('HEAD', 'GET'))
        self.assertEqual(config._added['request_method'], ('HEAD', 'GET'))
        self.assertTrue(config._actions)

    def test_view_isclass_with_attr(self):
        class AView(object):
            pass
        config = self._makeConfig()
        self._callFUT(config, view=AView, attr='foo')
        self.assertTrue(config.desc.startswith('method'))

    def test_discriminator(self):
        config = self._makeConfig()
        self._callFUT(config)
        discrim = config._actions[0][0]
        self.assertEqual(discrim.resolve(),
                         ('sdi view', None, '', 'substanced_manage', 'hash')
                         )

    def test_intr_action(self):
        config = self._makeConfig()
        self._callFUT(config)
        self.assertEqual(config._actions[0][1][0], config._intr)

    def test_intr_related(self):
        config = self._makeConfig()
        self._callFUT(config)
        self.assertTrue('views' in config._intr.related)

    def test_intr_values(self):
        config = self._makeConfig()
        self._callFUT(
            config,
            tab_title='tab_title',
            tab_condition='tab_condition',
            check_csrf=True
            )
        self.assertEqual(config._intr['tab_title'], 'tab_title')
        self.assertEqual(config._intr['tab_condition'], 'tab_condition')
        self.assertEqual(config._intr.related['views'].resolve(),
                         ('view', None, '', 'substanced_manage', 'hash'))

class Test_mgmt_path(unittest.TestCase):
    def _callFUT(self, *arg, **kw):
        from .. import mgmt_path
        return mgmt_path(*arg, **kw)

    def test_it(self):
        from .. import MANAGE_ROUTE_NAME
        request = testing.DummyRequest()
        context = testing.DummyResource()
        def route_path(route_name, *arg, **kw):
            self.assertEqual(route_name, MANAGE_ROUTE_NAME)
            self.assertEqual(arg, ('a',))
            self.assertEqual(kw, {'b':1, 'traverse':('',)})
            return '/path'
        request.route_path = route_path
        result = self._callFUT(request, context, 'a', b=1)
        self.assertEqual(result, '/path')

class Test_mgmt_url(unittest.TestCase):
    def _callFUT(self, *arg, **kw):
        from .. import mgmt_url
        return mgmt_url(*arg, **kw)

    def test_it(self):
        from .. import MANAGE_ROUTE_NAME
        request = testing.DummyRequest()
        context = testing.DummyResource()
        def route_url(route_name, *arg, **kw):
            self.assertEqual(route_name, MANAGE_ROUTE_NAME)
            self.assertEqual(arg, ('a',))
            self.assertEqual(kw, {'b':1, 'traverse':('',)})
            return 'http://example.com/path'
        request.route_url = route_url
        result = self._callFUT(request, context, 'a', b=1)
        self.assertEqual(result, 'http://example.com/path')


class Test_mgmt_view(unittest.TestCase):
    def setUp(self):
        testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _getTargetClass(self):
        from .. import mgmt_view
        return mgmt_view

    def _makeOne(self, *arg, **kw):
        return self._getTargetClass()(*arg, **kw)

    def test_create_defaults(self):
        decorator = self._makeOne()
        self.assertEqual(decorator.__dict__, {})

    def test_create_nondefaults(self):
        decorator = self._makeOne(
            name=None,
            request_type=None,
            permission='foo',
            mapper='mapper',
            decorator='decorator',
            match_param='match_param',
            )
        self.assertEqual(decorator.name, None)
        self.assertEqual(decorator.request_type, None)
        self.assertEqual(decorator.permission, 'foo')
        self.assertEqual(decorator.mapper, 'mapper')
        self.assertEqual(decorator.decorator, 'decorator')
        self.assertEqual(decorator.match_param, 'match_param')
        
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

class Test_sdi_mgmt_views(unittest.TestCase):
    def setUp(self):
        testing.setUp()

    def tearDown(self):
        testing.tearDown()
        
    def _callFUT(self, context, request, names=None):
        from .. import sdi_mgmt_views
        return sdi_mgmt_views(context, request, names)

    def test_context_has_no_name(self):
        result = self._callFUT(None, None)
        self.assertEqual(result, [])

    def test_no_views_found(self):
        request = testing.DummyRequest()
        request.matched_route = None
        request.registry.content = DummyContent()
        request.registry.introspector = DummyIntrospector()
        context = testing.DummyResource()
        result = self._callFUT(context, request)
        self.assertEqual(result, [])

    def test_no_related_view(self):
        request = testing.DummyRequest()
        request.matched_route = None
        request.registry.content = DummyContent()
        intr = {}
        intr['tab_title'] = None
        intr['tab_condition'] = None
        intr['tab_before'] = None
        intr['tab_after'] = None
        intr = DummyIntrospectable(related=(), introspectable=intr)
        request.registry.introspector = DummyIntrospector([(intr,)])
        context = testing.DummyResource()
        result = self._callFUT(context, request)
        self.assertEqual(result, [])

    def test_one_related_view_gardenpath(self):
        request = testing.DummyRequest()
        request.matched_route = None
        request.mgmt_path = lambda context, view_name: '/path/%s' % view_name
        request.registry.content = DummyContent()
        request.view_name = 'name'
        view_intr = DummyIntrospectable()
        view_intr.category_name = 'views'
        view_intr['name'] = 'name'
        view_intr['context'] = None
        view_intr['derived_callable'] = None
        intr = {}
        intr['tab_title'] = None
        intr['tab_condition'] = None
        intr['tab_before'] = None
        intr['tab_after'] = None
        intr = DummyIntrospectable(related=(view_intr,), introspectable=intr)
        request.registry.introspector = DummyIntrospector([(intr,)])
        context = testing.DummyResource()
        result = self._callFUT(context, request)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['view_name'], 'name')
        self.assertEqual(result[0]['title'], 'Name')
        self.assertEqual(result[0]['class'], 'active')
        self.assertEqual(result[0]['url'], '/path/@@name')

    def test_one_related_view_somecontext_tabcondition_None(self):
        from zope.interface import Interface
        class IFoo(Interface):
            pass
        request = testing.DummyRequest()
        request.matched_route = None
        request.mgmt_path = lambda context, view_name: '/path/%s' % view_name
        request.registry.content = DummyContent()
        view_intr = DummyIntrospectable()
        view_intr.category_name = 'views'
        view_intr['name'] = 'name'
        view_intr['context'] = IFoo
        view_intr['derived_callable'] = None
        intr = {}
        intr['tab_title'] = None
        intr['tab_condition'] = None
        intr['tab_before'] = None
        intr['tab_after'] = None
        intr = DummyIntrospectable(related=(view_intr,), introspectable=intr)
        request.registry.introspector = DummyIntrospector([(intr,)])
        context = testing.DummyResource()
        result = self._callFUT(context, request)
        self.assertEqual(result, [])

    def test_one_related_view_instcontext_tabcondition_None(self):
        class Foo(object):
            pass
        request = testing.DummyRequest()
        request.matched_route = None
        request.mgmt_path = lambda context, view_name: '/path/%s' % view_name
        request.registry.content = DummyContent()
        view_intr = DummyIntrospectable()
        view_intr.category_name = 'views'
        view_intr['name'] = 'name'
        view_intr['context'] = Foo
        view_intr['derived_callable'] = None
        intr = {}
        intr['tab_title'] = None
        intr['tab_condition'] = None
        intr['tab_before'] = None
        intr['tab_after'] = None
        intr = DummyIntrospectable(related=(view_intr,), introspectable=intr)
        request.registry.introspector = DummyIntrospector([(intr,)])
        context = testing.DummyResource()
        result = self._callFUT(context, request)
        self.assertEqual(result, [])

    def test_one_related_view_anycontext_tabcondition_False(self):
        request = testing.DummyRequest()
        request.matched_route = None
        request.mgmt_path = lambda context, view_name: '/path/%s' % view_name
        request.registry.content = DummyContent()
        view_intr = DummyIntrospectable()
        view_intr.category_name = 'views'
        view_intr['name'] = 'name'
        view_intr['context'] = None
        view_intr['derived_callable'] = None
        intr = {}
        intr['tab_title'] = None
        intr['tab_condition'] = False
        intr['tab_before'] = None
        intr['tab_after'] = None
        intr = DummyIntrospectable(related=(view_intr,), introspectable=intr)
        request.registry.introspector = DummyIntrospector([(intr,)])
        context = testing.DummyResource()
        result = self._callFUT(context, request)
        self.assertEqual(result, [])

    def test_one_related_view_anycontext_tabcondition_True(self):
        request = testing.DummyRequest()
        request.matched_route = None
        request.mgmt_path = lambda context, view_name: '/path/%s' % view_name
        request.registry.content = DummyContent()
        view_intr = DummyIntrospectable()
        view_intr.category_name = 'views'
        view_intr['name'] = 'name'
        view_intr['context'] = None
        view_intr['derived_callable'] = None
        intr = {}
        intr['tab_title'] = None
        intr['tab_condition'] = True
        intr['tab_before'] = None
        intr['tab_after'] = None
        intr = DummyIntrospectable(related=(view_intr,), introspectable=intr)
        request.registry.introspector = DummyIntrospector([(intr,)])
        context = testing.DummyResource()
        result = self._callFUT(context, request)
        self.assertEqual(len(result), 1)

    def test_one_related_view_anycontext_tabcondition_callable(self):
        request = testing.DummyRequest()
        request.matched_route = None
        request.mgmt_path = lambda context, view_name: '/path/%s' % view_name
        request.registry.content = DummyContent()
        view_intr = DummyIntrospectable()
        view_intr.category_name = 'views'
        view_intr['name'] = 'name'
        view_intr['context'] = None
        view_intr['derived_callable'] = None
        intr = {}
        def tabcondition(context, request):
            return False
        intr['tab_title'] = None
        intr['tab_condition'] = tabcondition
        intr['tab_before'] = None
        intr['tab_after'] = None
        intr = DummyIntrospectable(related=(view_intr,), introspectable=intr)
        request.registry.introspector = DummyIntrospector([(intr,)])
        context = testing.DummyResource()
        result = self._callFUT(context, request)
        self.assertEqual(result, [])

    def test_one_related_view_anycontext_tabcondition_None_not_in_names(self):
        request = testing.DummyRequest()
        request.matched_route = None
        request.mgmt_path = lambda context, view_name: '/path/%s' % view_name
        request.registry.content = DummyContent()
        view_intr = DummyIntrospectable()
        view_intr.category_name = 'views'
        view_intr['name'] = 'name'
        view_intr['context'] = None
        view_intr['derived_callable'] = None
        intr = {}
        intr['tab_title'] = None
        intr['tab_condition'] = None
        intr['tab_before'] = None
        intr['tab_after'] = None
        intr = DummyIntrospectable(related=(view_intr,), introspectable=intr)
        request.registry.introspector = DummyIntrospector([(intr,)])
        context = testing.DummyResource()
        result = self._callFUT(context, request, names=('fred',))
        self.assertEqual(result, [])

    def test_one_related_view_anycontext_tabcondition_None_predicatefail(self):
        request = testing.DummyRequest()
        request.matched_route = None
        request.mgmt_path = lambda context, view_name: '/path/%s' % view_name
        request.registry.content = DummyContent()
        view_intr = DummyIntrospectable()
        view_intr.category_name = 'views'
        view_intr['name'] = 'name'
        view_intr['context'] = None
        class Thing(object):
            def __predicated__(self, context, request):
                return False
        thing = Thing()
        view_intr['derived_callable'] = thing
        intr = {}
        intr['tab_title'] = None
        intr['tab_condition'] = None
        intr['tab_before'] = None
        intr['tab_after'] = None
        intr = DummyIntrospectable(related=(view_intr,), introspectable=intr)
        request.registry.introspector = DummyIntrospector([(intr,)])
        context = testing.DummyResource()
        result = self._callFUT(context, request)
        self.assertEqual(result, [])

    def test_one_related_view_anycontext_tabcondition_None_permissionfail(self):
        request = testing.DummyRequest()
        request.matched_route = None
        request.mgmt_path = lambda context, view_name: '/path/%s' % view_name
        request.registry.content = DummyContent()
        view_intr = DummyIntrospectable()
        view_intr.category_name = 'views'
        view_intr['name'] = 'name'
        view_intr['context'] = None
        class Thing(object):
            def __permitted__(self, context, request):
                return False
        thing = Thing()
        view_intr['derived_callable'] = thing
        intr = {}
        intr['tab_title'] = None
        intr['tab_condition'] = None
        intr['tab_before'] = None
        intr['tab_after'] = None
        intr = DummyIntrospectable(related=(view_intr,), introspectable=intr)
        request.registry.introspector = DummyIntrospector([(intr,)])
        context = testing.DummyResource()
        result = self._callFUT(context, request)
        self.assertEqual(result, [])

    def test_one_related_view_two_tabs_gardenpath_tab_title_sorting(self):
        request = testing.DummyRequest()
        request.matched_route = None
        request.mgmt_path = lambda context, view_name: '/path/%s' % view_name
        request.registry.content = DummyContent()
        view_intr = DummyIntrospectable()
        view_intr.category_name = 'views'
        view_intr['name'] = 'name'
        view_intr['context'] = None
        view_intr['derived_callable'] = None
        intr = {}
        intr['tab_title'] = 'b'
        intr['tab_condition'] = None
        intr['tab_before'] = None
        intr['tab_after'] = None
        intr2 = {}
        intr2['tab_title'] = 'a'
        intr2['tab_condition'] = None
        intr2['tab_before'] = None
        intr2['tab_after'] = None
        intr = DummyIntrospectable(related=(view_intr,), introspectable=intr)
        intr2 = DummyIntrospectable(related=(view_intr,), introspectable=intr2)
        request.registry.introspector = DummyIntrospector([(intr, intr2)])
        context = testing.DummyResource()
        result = self._callFUT(context, request)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['view_name'], 'name')
        self.assertEqual(result[0]['title'], 'b')
        self.assertEqual(result[0]['class'], None)
        self.assertEqual(result[0]['url'], '/path/@@name')
        # "a" is gone because we use topological sorting and it conflates
        # view data with the same view name

    def test_one_related_view_gardenpath_with_taborder(self):
        request = testing.DummyRequest()
        request.matched_route = None
        request.mgmt_path = lambda context, view_name: '/path/%s' % view_name
        request.registry.content = DummyContent(tab_order=('b',))
        request.view_name = 'b'
        view_intr1 = DummyIntrospectable()
        view_intr1.category_name = 'views'
        view_intr1['name'] = 'b'
        view_intr1['context'] = None
        view_intr1['derived_callable'] = None
        view_intr2 = DummyIntrospectable()
        view_intr2.category_name = 'views'
        view_intr2['name'] = 'a'
        view_intr2['context'] = None
        view_intr2['derived_callable'] = None
        intr = {}
        intr['tab_title'] = 'b'
        intr['tab_condition'] = None
        intr['tab_before'] = None
        intr['tab_after'] = None
        intr2 = {}
        intr2['tab_title'] = 'a'
        intr2['tab_condition'] = None
        intr2['tab_before'] = None
        intr2['tab_after'] = None
        intr = DummyIntrospectable(related=(view_intr1,), introspectable=intr)
        intr2 = DummyIntrospectable(related=(view_intr2,), introspectable=intr2)
        request.registry.introspector = DummyIntrospector([(intr, intr2)])
        context = testing.DummyResource()
        result = self._callFUT(context, request)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['view_name'], 'b')
        self.assertEqual(result[0]['title'], 'b')
        self.assertEqual(result[0]['class'], 'active')
        self.assertEqual(result[0]['url'], '/path/@@b')
        self.assertEqual(result[1]['view_name'], 'a')
        self.assertEqual(result[1]['title'], 'a')
        self.assertEqual(result[1]['class'], None)
        self.assertEqual(result[1]['url'], '/path/@@a')

    def test_one_related_view_gardenpath_with_tab_before(self):
        request = testing.DummyRequest()
        request.matched_route = None
        request.mgmt_path = lambda context, view_name: '/path/%s' % view_name
        request.registry.content = DummyContent()
        request.view_name = 'b'
        view_intr1 = DummyIntrospectable()
        view_intr1.category_name = 'views'
        view_intr1['name'] = 'b'
        view_intr1['context'] = None
        view_intr1['derived_callable'] = None
        view_intr2 = DummyIntrospectable()
        view_intr2.category_name = 'views'
        view_intr2['name'] = 'a'
        view_intr2['context'] = None
        view_intr2['derived_callable'] = None
        intr = {}
        intr['tab_title'] = 'b'
        intr['tab_condition'] = None
        intr['tab_before'] = 'a'
        intr['tab_after'] = None
        intr2 = {}
        intr2['tab_title'] = 'a'
        intr2['tab_condition'] = None
        intr2['tab_before'] = None
        intr2['tab_after'] = None
        intr = DummyIntrospectable(related=(view_intr1,), introspectable=intr)
        intr2 = DummyIntrospectable(related=(view_intr2,), introspectable=intr2)
        request.registry.introspector = DummyIntrospector([(intr, intr2)])
        context = testing.DummyResource()
        result = self._callFUT(context, request)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]['view_name'], 'b')
        self.assertEqual(result[0]['title'], 'b')
        self.assertEqual(result[0]['class'], 'active')
        self.assertEqual(result[0]['url'], '/path/@@b')
        self.assertEqual(result[1]['view_name'], 'a')
        self.assertEqual(result[1]['title'], 'a')
        self.assertEqual(result[1]['class'], None)
        self.assertEqual(result[1]['url'], '/path/@@a')

class Test_sdi_folder_contents(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _callFUT(self, context, request):
        from .. import sdi_folder_contents
        return sdi_folder_contents(context, request)

    def _makeRequest(self):
        request = testing.DummyRequest()
        request.registry.content = DummyContent(columns=None, icon=None)
        request.mgmt_path = lambda *arg: '/manage'
        return request
        
    def test_no_permissions(self):
        self.config.testing_securitypolicy(permissive=False)
        context = testing.DummyResource()
        context['a'] = testing.DummyResource()
        request = self._makeRequest()
        result = list(self._callFUT(context, request))
        self.assertEqual(len(result), 0)

    def test_all_permissions(self):
        self.config.testing_securitypolicy(permissive=True)
        context = testing.DummyResource()
        context['a'] = testing.DummyResource()
        request = self._makeRequest()
        request.registry.content = DummyContent(icon='icon')
        result = list(self._callFUT(context, request))
        self.assertEqual(len(result), 1)
        item = result[0]
        self.assertEqual(item['url'], '/manage')
        self.assertTrue(item['viewable'])
        self.assertTrue(item['deletable'])
        self.assertEqual(item['icon'], 'icon')
        self.assertEqual(item['name'], 'a')

    def test_computable_icon(self):
        self.config.testing_securitypolicy(permissive=True)
        context = testing.DummyResource()
        context['a'] = testing.DummyResource()
        request = self._makeRequest()
        def icon(subobject, _request):
            self.assertEqual(subobject, context['a'])
            self.assertEqual(_request, request)
            return 'anicon'
        request.registry.content = DummyContent(icon=icon)
        result = list(self._callFUT(context, request))
        self.assertEqual(len(result), 1)
        item = result[0]
        self.assertEqual(item['url'], '/manage')
        self.assertTrue(item['viewable'])
        self.assertTrue(item['deletable'])
        self.assertEqual(item['icon'], 'anicon')
        self.assertEqual(item['name'], 'a')

    def test_literal_icon(self):
        self.config.testing_securitypolicy(permissive=True)
        context = testing.DummyResource()
        context['a'] = testing.DummyResource()
        request = self._makeRequest()
        request.registry.content = DummyContent(icon='anicon')
        result = list(self._callFUT(context, request))
        self.assertEqual(len(result), 1)
        item = result[0]
        self.assertEqual(item['url'], '/manage')
        self.assertTrue(item['viewable'])
        self.assertTrue(item['deletable'])
        self.assertEqual(item['icon'], 'anicon')
        self.assertEqual(item['name'], 'a')

    def test_all_permissions_hidden_subobject(self):
        self.config.testing_securitypolicy(permissive=True)
        context = testing.DummyResource()
        resource = testing.DummyResource()
        resource.__sdi_hidden__ = lambda *arg: True
        context['object'] = resource
        request = self._makeRequest()
        result = list(self._callFUT(context, request))
        self.assertEqual(len(result), 0)

    def test_all_permissions_hidden_subobject_boolean(self):
        self.config.testing_securitypolicy(permissive=True)
        context = testing.DummyResource()
        resource = testing.DummyResource()
        resource.__sdi_hidden__ = True
        context['object'] = resource
        request = self._makeRequest()
        result = list(self._callFUT(context, request))
        self.assertEqual(len(result), 0)

    def test_deletable_callable(self):
        self.config.testing_securitypolicy(permissive=True)
        context = testing.DummyResource()
        resource = testing.DummyResource()
        resource.__sdi_deletable__ = lambda *arg: False
        context['object'] = resource
        request = self._makeRequest()
        result = list(self._callFUT(context, request))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['deletable'], False)

    def test_deletable_boolean(self):
        self.config.testing_securitypolicy(permissive=True)
        context = testing.DummyResource()
        resource = testing.DummyResource()
        resource.__sdi_deletable__ = False
        context['object'] = resource
        request = self._makeRequest()
        result = list(self._callFUT(context, request))
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]['deletable'], False)

    def test_columns_callable(self):
        def get_columns(folder, subobject, request, default_columns):
            self.assertEqual(len(default_columns), 1)
            return [{'name': 'Col 1',
                     'value': getattr(subobject, 'col1')},
                    {'name': 'Col 2',
                     'value': getattr(subobject, 'col2')}]
        self.config.testing_securitypolicy(permissive=True)
        context = testing.DummyResource()
        context['a'] = testing.DummyResource()
        context['a'].col1 = 'val1'
        context['a'].col2 = 'val2'
        request = self._makeRequest()
        request.registry.content = DummyContent(columns=get_columns)
        result = list(self._callFUT(context, request))
        self.assertEqual(result[0]['columns'], ['val1', 'val2'])

class Test_default_sdi_addable(unittest.TestCase):
    def _callFUT(self, context, intr):
        from .. import default_sdi_addable
        return default_sdi_addable(context, intr)

    def test_is_service_with_service_name_in_context(self):
        context = {'catalog':True}
        intr = {'meta':{'is_service':True, 'service_name':'catalog'}}
        self.assertFalse(self._callFUT(context, intr))
                         
    def test_is_service_with_service_name_not_in_context(self):
        context = {}
        intr = {'meta':{'is_service':True, 'service_name':'catalog'}}
        self.assertTrue(self._callFUT(context, intr))
    
    def test_is_service_without_service_name(self):
        context = {'catalog':True}
        intr = {'meta':{'is_service':True}}
        self.assertTrue(self._callFUT(context, intr))

    def test_is_not_service(self):
        context = {'catalog':True}
        intr = {'meta':{}}
        self.assertTrue(self._callFUT(context, intr))

class Test_default_sdi_columns(unittest.TestCase):
    def _callFUT(self, folder, context, request):
        from .. import default_sdi_columns
        return default_sdi_columns(folder, context, request)
    
    def _makeRequest(self, icon):
        request = testing.DummyResource()
        registry = testing.DummyResource()
        content = testing.DummyResource()
        content.metadata = lambda *arg: icon
        request.registry = registry
        request.registry.content = content
        request.mgmt_path = lambda *arg: '/'
        return request

    def test_it(self):
        fred = testing.DummyResource()
        fred.__name__ = 'fred'
        request = self._makeRequest('icon')
        result = self._callFUT(None, fred, request)
        self.assertEqual(
           result,
           [{'sortable': True, 
             'name': 'Name', 
             'value': '<i class="icon"> </i> <a href="/">fred</a>'}] 
           )

    def test_it_with_callable_icon(self):
        fred = testing.DummyResource()
        fred.__name__ = 'fred'
        request = self._makeRequest(lambda *arg: 'icon')
        result = self._callFUT(None, fred, request)
        self.assertEqual(
           result, 
           [{'sortable': True, 
             'name': 'Name', 
             'value': '<i class="icon"> </i> <a href="/">fred</a>'}] 
           )

class Test_default_sdi_buttons(unittest.TestCase):
    def _callFUT(self, context, request):
        from .. import default_sdi_buttons
        return default_sdi_buttons(context, request)
    
    def test_it_novals(self):
        request = testing.DummyRequest()
        context = testing.DummyResource()
        result = self._callFUT(context, request)
        self.assertEqual(
            result,
            [{
              'type': 'group', 
              'buttons': 
                  [{'text': 'Rename', 
                    'class': '', 
                    'id': 'rename', 
                    'value': 'rename', 
                    'name': 'form.rename'}, 
                   {'text': 'Copy', 'class': '', 
                    'id': 'copy', 
                    'value': 'copy', 
                    'name': 'form.copy'}, 
                   {'text': 'Move', 
                    'class': '', 
                    'id': 'move', 
                    'value': 'move', 
                    'name': 'form.move'}, 
                   {'text': 'Duplicate', 
                    'class': '', 
                    'id': 'duplicate', 
                    'value': 'duplicate', 
                    'name': 'form.duplicate'}]
                }, 
             {
              'type':'group',
              'buttons': 
                  [{'text': 'Delete', 
                    'class': 'btn-danger', 
                    'id': 'delete', 
                    'value': 'delete', 
                    'name': 'form.delete'}]
               },
            ])


    def test_it_tocopy(self):
        request = testing.DummyRequest()
        context = testing.DummyResource()
        request.session['tocopy'] = True
        result = self._callFUT(context, request)
        self.assertEqual(
            result,
            [
              {'buttons': 
                [{'text': 'Copy here', 
                  'class': 'btn-primary', 
                  'id': 'copy_finish', 
                  'value': 'copy_finish', 
                  'name': 'form.copy_finish'}, 
                 {'text': 'Cancel', 
                  'class': 'btn-danger', 
                  'id': 'cancel', 
                  'value': 'cancel', 
                  'name': 'form.copy_finish'}],
               'type': 'single'}
               ]
               )

    def test_it_tomove(self):
        request = testing.DummyRequest()
        context = testing.DummyResource()
        request.session['tomove'] = True
        result = self._callFUT(context, request)
        self.assertEqual(
            result, [
            {'buttons': [
                {'text': 'Move here',
                 'class': 'btn-primary',
                 'id': 'move_finish',
                 'value': 'move_finish',
                 'name': 'form.move_finish'},
                {'text': 'Cancel',
                 'class': 'btn-danger',
                 'id': 'cancel',
                 'value': 'cancel',
                 'name':'form.move_finish'}],
             'type': 'single'}
            ]            
            )


class Test_sdi_add_views(unittest.TestCase):
    def _callFUT(self, context, request):
        from .. import sdi_add_views
        return sdi_add_views(context, request)

    def setUp(self):
        testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def test_no_content_types(self):
        request = testing.DummyRequest()
        request.matched_route = None
        request.registry.content = DummyContent()
        request.registry.introspector = DummyIntrospector()
        result = self._callFUT(None, request)
        self.assertEqual(result, [])

    def test_one_content_type(self):
        request = testing.DummyRequest()
        request.matched_route = None
        request.registry.content = DummyContent()
        request.mgmt_path = lambda *arg: '/path'
        ct_intr = {}
        ct_intr['meta'] = {'add_view':'abc'}
        ct_intr['content_type'] = 'Content'
        ct_intr = DummyIntrospectable(introspectable=ct_intr)
        view_intr1 = DummyIntrospectable()
        view_intr1.category_name = 'views'
        view_intr1['name'] = 'abc'
        view_intr1['context'] = None
        view_intr1['derived_callable'] = None
        intr = {}
        intr['tab_title'] = 'abc'
        intr['tab_condition'] = None
        intr['tab_before'] = None
        intr['tab_after'] = None
        intr = DummyIntrospectable(related=(view_intr1,), introspectable=intr)
        request.registry.introspector = DummyIntrospector([(ct_intr,), (intr,)])
        context = testing.DummyResource()
        result = self._callFUT(context, request)
        self.assertEqual(
            result,
            [{'url': '/path', 'type_name': 'Content', 'icon': ''}])

    def test_one_content_type_not_addable(self):
        request = testing.DummyRequest()
        request.matched_route = None
        request.registry.content = DummyContent()
        request.mgmt_path = lambda *arg: '/path'
        context = testing.DummyResource()
        context.__sdi_addable__ = ('Not Content',)
        ct_intr = {}
        ct_intr['meta'] = {'add_view':'abc'}
        ct_intr['content_type'] = 'Content'
        ct_intr = DummyIntrospectable(introspectable=ct_intr)
        view_intr1 = DummyIntrospectable()
        view_intr1.category_name = 'views'
        view_intr1['name'] = 'abc'
        view_intr1['context'] = None
        view_intr1['derived_callable'] = None
        intr = {}
        intr['tab_title'] = 'abc'
        intr['tab_condition'] = None
        intr['tab_before'] = None
        intr['tab_after'] = None
        intr = DummyIntrospectable(related=(view_intr1,), introspectable=intr)
        request.registry.introspector = DummyIntrospector([(ct_intr,), (intr,)])
        result = self._callFUT(context, request)
        self.assertEqual(result, [])

    def test_one_content_type_not_addable_callable(self):
        request = testing.DummyRequest()
        request.matched_route = None
        request.registry.content = DummyContent()
        request.mgmt_path = lambda *arg: '/path'
        context = testing.DummyResource()
        context.__sdi_addable__ = lambda *arg: False
        ct_intr = {}
        ct_intr['meta'] = {'add_view':'abc'}
        ct_intr['content_type'] = 'Content'
        ct_intr = DummyIntrospectable(introspectable=ct_intr)
        view_intr1 = DummyIntrospectable()
        view_intr1.category_name = 'views'
        view_intr1['name'] = 'abc'
        view_intr1['context'] = None
        view_intr1['derived_callable'] = None
        intr = {}
        intr['tab_title'] = 'abc'
        intr['tab_condition'] = None
        intr['tab_before'] = None
        intr['tab_after'] = None
        intr = DummyIntrospectable(related=(view_intr1,), introspectable=intr)
        request.registry.introspector = DummyIntrospector([(ct_intr,), (intr,)])
        result = self._callFUT(context, request)
        self.assertEqual(result, [])
        
    def test_content_type_not_addable_to(self):
        request = testing.DummyRequest()
        request.matched_route = None
        request.registry.content = DummyContent()
        request.mgmt_path = lambda *arg: '/path'
        context = testing.DummyResource()
        context.__content_type__ = 'Foo'
        ct_intr = {}
        ct_intr['meta'] = {'add_view':lambda *arg: 'abc'}
        ct_intr['content_type'] = 'Content'
        ct_intr = DummyIntrospectable(introspectable=ct_intr)
        ct2_intr = {}
        checked = []
        def check(context, request):
            checked.append(True)
        ct2_intr['meta'] = {'add_view':check}
        ct2_intr['content_type'] = 'Content'
        ct2_intr = DummyIntrospectable(introspectable=ct2_intr)
        view_intr1 = DummyIntrospectable()
        view_intr1.category_name = 'views'
        view_intr1['name'] = 'abc'
        view_intr1['context'] = None
        view_intr1['derived_callable'] = None
        intr = {}
        intr['tab_title'] = 'abc'
        intr['tab_condition'] = None
        intr['tab_before'] = None
        intr['tab_after'] = None
        intr = DummyIntrospectable(related=(view_intr1,), introspectable=intr)
        request.registry.introspector = DummyIntrospector(
            [(ct_intr, ct2_intr), (intr,)])
        result = self._callFUT(context, request)
        self.assertEqual(checked, [True])
        self.assertEqual(
            result,
            [{'url': '/path', 'type_name': 'Content', 'icon': ''}])

class Test_get_user(unittest.TestCase):
    def _callFUT(self, request):
        from .. import get_user
        return get_user(request)

    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def test_userid_is_None(self):
        self.config.testing_securitypolicy(permissive=False)
        request = testing.DummyRequest()
        self.assertEqual(self._callFUT(request), None)

    def test_userid_is_not_None(self):
        from ...interfaces import IFolder
        self.config.testing_securitypolicy(permissive=True, userid='fred')
        request = testing.DummyRequest()
        context = testing.DummyResource(__provides__=IFolder)
        objectmap = testing.DummyResource()
        objectmap.object_for = lambda *arg: 'foo'
        context.__objectmap__ = objectmap
        request.context = context
        self.assertEqual(self._callFUT(request), 'foo')

class TestFlashUndo(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
        
    def _makeOne(self, request):
        from .. import FlashUndo
        return FlashUndo(request)

    def test_no_permission(self):
        self.config.testing_securitypolicy(permissive=False)
        request = testing.DummyRequest()
        inst = self._makeOne(request)
        connection = DummyConnection()
        inst.get_connection = lambda *arg: connection
        inst.transaction = DummyTransaction()
        inst('message')
        self.assertEqual(request.session['_f_'], ['message'])
        self.assertFalse(inst.transaction.notes)

    def test_db_doesnt_support_undo(self):
        self.config.testing_securitypolicy(permissive=True)
        request = testing.DummyRequest()
        inst = self._makeOne(request)
        connection = DummyConnection(supports_undo=False)
        inst.get_connection = lambda *arg: connection
        inst.transaction = DummyTransaction()
        inst('message')
        self.assertEqual(request.session['_f_'], ['message'])
        self.assertFalse(inst.transaction.notes)

    def test_it(self):
        self.config.testing_securitypolicy(permissive=True)
        request = testing.DummyRequest()
        request.mgmt_path = lambda *arg, **kw: '/mg'
        inst = self._makeOne(request)
        connection = DummyConnection()
        inst.get_connection = lambda *arg: connection
        inst.transaction = DummyTransaction()
        inst('message')
        self.assertEqual(request.session['_f_'],
                         [u'<span>message <a href="/mg" class="btn btn-mini '
                          u'btn-info">Undo</a></span>\n'])
        self.assertTrue(inst.transaction.notes)

class DummyContent(object):
    def __init__(self, **kw):
        self.__dict__.update(kw)
        
    def metadata(self, context, name, default=None):
        return getattr(self, name, default)

class DummyIntrospector(object):
    def __init__(self, results=()):
        self.results = list(results)
        
    def get_category(self, *arg):
        if self.results:
            return self.results.pop(0)
        return ()

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

class DummyPredicateList(object):
    def make(self, config, **pvals):
        return 1, (), 'hash'

class DummyConfigurator(object):
    _ainfo = None
    def __init__(self):
        self._intr = DummyIntrospectable()
        self._actions = []
        self._added = None
        self.get_predlist = lambda *arg: DummyPredicateList()

    def object_description(self, ob):
        return ob
        
    def maybe_dotted(self, thing):
        return thing

    def add_view(self, **kw):
        self._added = kw

    def add_mgmt_view(self, view=None, **settings):
        self.view = view
        self.settings = settings

    def with_package(self, other):
        return self

    def introspectable(self, category, discrim, desc, name):
        self.desc = desc
        return self._intr

    def action(self, discriminator, introspectables):
        self._actions.append((discriminator, introspectables))
    
class DummyIntrospectable(dict):
    def __init__(self, **kw):
        dict.__init__(self, **kw)
        self.related = {}
        
    def relate(self, category, discrim):
        self.related[category] = discrim

class Dummy(object):
    pass

class DummyDB(object):
    def __init__(self, supports_undo, undo_info, undo_exc=None):
        self.supports_undo = supports_undo
        self.undo_info = undo_info
        self.undone = []
        self.undo_exc = undo_exc

    def supportsUndo(self):
        return self.supports_undo

class DummyConnection(object):
    def __init__(self, supports_undo=True, undo_info=(), undo_exc=None):
        self._db = DummyDB(supports_undo, undo_info, undo_exc)

    def db(self):
        return self._db

class DummyTransaction(object):
    def __init__(self):
        self.notes = []
        
    def get(self):
        return self

    def note(self, note):
        self.notes.append(note)

