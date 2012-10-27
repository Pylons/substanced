import unittest
from pyramid import testing

class Test_add_catalog_service(unittest.TestCase):
    def _callFUT(self, context, request):
        from ..catalog import add_catalog_service
        return add_catalog_service(context, request)

    def test_it(self):
        context = testing.DummyResource()
        request = testing.DummyRequest()
        request.mgmt_path = lambda *arg: '/'
        service = testing.DummyResource()
        request.registry.content = DummyContentRegistry(service)
        result = self._callFUT(context, request)
        self.assertEqual(context['catalog'], service)
        self.assertEqual(result.location, '/')

class TestManageCatalog(unittest.TestCase):
    def _makeOne(self, context, request):
        from ..catalog import ManageCatalog
        return ManageCatalog(context, request)

    def test_view(self):
        context = DummyCatalog()
        request = testing.DummyRequest()
        request.mgmt_path = lambda *arg: '/manage'
        inst = self._makeOne(context, request)
        result = inst.view()
        self.assertEqual(result['cataloglen'], 0)

    def test_reindex(self):
        context = DummyCatalog()
        request = testing.DummyRequest()
        request.mgmt_path = lambda *arg: '/manage'
        inst = self._makeOne(context, request)
        result = inst.reindex()
        self.assertEqual(result.location, '/manage')
        self.assertEqual(context.reindexed, None)

class TestManageIndex(unittest.TestCase):
    def _makeOne(self, context, request):
        from ..catalog import ManageIndex
        return ManageIndex(context, request)

    def test_view(self):
        context = DummyIndex()
        request = testing.DummyRequest()
        request.mgmt_path = lambda *arg: '/manage'
        inst = self._makeOne(context, request)
        result = inst.view()
        self.assertEqual(result['indexed'], 1)
        self.assertEqual(result['not_indexed'], 1)
        self.assertEqual(result['index_name'], 'name')
        self.assertEqual(result['index_type'], 'DummyIndex')

    def test_reindex_parent_not_icatalog(self):
        context = DummyIndex(False)
        request = testing.DummyRequest()
        request.mgmt_path = lambda *arg: '/manage'
        inst = self._makeOne(context, request)
        result = inst.reindex()
        self.assertEqual(result.location, '/manage')
        self.assertEqual(
            request.session['_f_error'],
            ['Cannot reindex an index unless it is contained in a catalog'])

    def test_reindex_parent_is_icatalog(self):
        from zope.interface import alsoProvides
        from substanced.interfaces import ICatalog
        catalog = DummyCatalog()
        alsoProvides(catalog, ICatalog)
        context = DummyIndex(catalog)
        request = testing.DummyRequest()
        request.mgmt_path = lambda *arg: '/manage'
        inst = self._makeOne(context, request)
        result = inst.reindex()
        self.assertEqual(result.location, '/manage')
        self.assertEqual(catalog.indexes, ['name'])
        self.assertEqual(
            request.session['_f_success'], ['Index "name" reindexed'])

class TestSearchCatalogView(unittest.TestCase):
    def _makeOne(self, context, request):
        from ..catalog import SearchCatalogView
        return SearchCatalogView(context, request)

    def test_search_success(self):
        request = testing.DummyRequest()
        context = testing.DummyResource()
        request.mgmt_path = lambda *arg, **kw: '/mg'
        inst = self._makeOne(context, request)
        resp = inst.search_success({'a':1})
        self.assertEqual(request.session['catalogsearch.appstruct'], {'a':1})
        self.assertEqual(resp.location, '/mg')

    def test_show_no_appstruct(self):
        request = testing.DummyRequest()
        context = testing.DummyResource()
        form = DummyForm()
        inst = self._makeOne(context, request)
        result = inst.show(form)
        self.assertEqual(result, {'searchresults': (),
                                  'form':'form'})

    def test_show_with_appstruct_no_results(self):
        request = testing.DummyRequest()
        context = testing.DummyResource()
        appstruct = {'cqe_expression':"name=='abc'"}
        request.session['catalogsearch.appstruct'] = appstruct
        form = DummyForm()
        inst = self._makeOne(context, request)
        q = DummyQuery([])
        objectmap = DummyObjectmap()
        def parse_query(expr, catalog):
            return q
        def find_objectmap(context):
            return objectmap 
        inst.parse_query = parse_query
        inst.find_objectmap = find_objectmap
        result = inst.show(form)
        self.assertEqual(result, {'searchresults': [('', 'No results')],
                                  'form':'form'})
        self.assertEqual(request.session['_f_success'], ['Query succeeded'])

    def test_show_with_appstruct_and_results(self):
        request = testing.DummyRequest()
        context = testing.DummyResource()
        appstruct = {'cqe_expression':"name=='abc'"}
        request.session['catalogsearch.appstruct'] = appstruct
        form = DummyForm()
        inst = self._makeOne(context, request)
        q = DummyQuery([1,2])
        objectmap = DummyObjectmap()
        def parse_query(expr, catalog):
            return q
        def find_objectmap(context):
            return objectmap 
        inst.parse_query = parse_query
        inst.find_objectmap = find_objectmap
        result = inst.show(form)
        self.assertEqual(result, {'searchresults': [(1,1), (2,2)],
                                  'form':'form'})
        self.assertEqual(request.session['_f_success'], ['Query succeeded'])

    def test_show_with_appstruct_query_exception(self):
        request = testing.DummyRequest()
        context = testing.DummyResource()
        appstruct = {'cqe_expression':"name=='abc'"}
        request.session['catalogsearch.appstruct'] = appstruct
        form = DummyForm()
        inst = self._makeOne(context, request)
        inst.logger = DummyLogger()
        result = inst.show(form)
        self.assertEqual(result, {'searchresults': (),
                                  'form':'form'})
        self.assertEqual(request.session['_f_error'],
                         ['Query failed (KeyError: name)'])

class Test_content_is_an_index(unittest.TestCase):
    def setUp(self):
        testing.setUp()
    def tearDown(self):
        testing.tearDown()

    def _callFUT(self, context, request):
        from ..catalog import context_is_an_index
        return context_is_an_index(context, request)
    
    def test_it_true(self):
        request = testing.DummyRequest()
        request.registry.content = DummyContent(True)
        context = testing.DummyResource()
        self.assertEqual(self._callFUT(context, request), True)
        
    def test_it_false(self):
        request = testing.DummyRequest()
        request.registry.content = DummyContent(False)
        context = testing.DummyResource()
        self.assertEqual(self._callFUT(context, request), False)

class Test_AddIndexView(unittest.TestCase):
    def setUp(self):
        testing.setUp()
    def tearDown(self):
        testing.tearDown()

    def _makeOne(self, context, request):
        from ..catalog import _AddIndexView
        return _AddIndexView(context, request)

    def test_add_success_no_reindex(self):
        context = testing.DummyResource()
        request = testing.DummyRequest()
        request.mgmt_path = lambda *arg: '/'
        inst = self._makeOne(context, request)
        index = testing.DummyResource()
        inst.makeindex = lambda *arg: index
        appstruct = {'name':'name', 'category':'category', 'reindex':False}
        result = inst.add_success(appstruct)
        self.assertEqual(result.location, '/')
        self.assertEqual(context['name'], index)
        self.assertEqual(index.sd_category, 'category')
        
    def test_add_success_with_reindex(self):
        context = testing.DummyResource()
        def reindex(indexes, registry):
            self.assertEqual(indexes, ('name',))
            registry.reindexed = True
        context.reindex = reindex
        request = testing.DummyRequest()
        request.mgmt_path = lambda *arg: '/'
        inst = self._makeOne(context, request)
        index = testing.DummyResource()
        inst.makeindex = lambda *arg: index
        appstruct = {'name':'name', 'category':'category', 'reindex':True}
        inst.add_success(appstruct)
        self.assertEqual(request.registry.reindexed, True)

    def test_makeindex(self):
        context = testing.DummyResource()
        request = testing.DummyRequest()
        inst = self._makeOne(context, request)
        inst.index_type_name = 'Foo Index'
        appstruct = {'name':'name'}
        index = testing.DummyResource()
        content = DummyContent(index)
        request.registry.content = content
        result = inst.makeindex(appstruct, request.registry)
        self.assertEqual(result, index)
        self.assertEqual(content.type_name, 'Foo Index')
        self.assertEqual(content.arg[0].method_name, 'name')

    def test_title(self):
        context = testing.DummyResource()
        request = testing.DummyRequest()
        inst = self._makeOne(context, request)
        inst.index_type_name = 'Foo Index'
        self.assertEqual(inst.title, 'Add Foo Index')

class TestAddPathIndexView(unittest.TestCase):
    def setUp(self):
        testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _makeOne(self, context, request):
        from ..catalog import AddPathIndexView
        return AddPathIndexView(context, request)

    def test_makeindex(self):
        context = testing.DummyResource()
        request = testing.DummyRequest()
        registry = request.registry
        index = 'abc'
        registry.content = DummyContent(index)
        inst = self._makeOne(context, request)
        result = inst.makeindex({}, request.registry)
        self.assertEqual(registry.content.type_name, 'Path Index')
        self.assertEqual(result, index)

class TestAddAllowedIndexView(unittest.TestCase):
    def setUp(self):
        testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _makeOne(self, context, request):
        from ..catalog import AddAllowedIndexView
        return AddAllowedIndexView(context, request)

    def test_makeindex(self):
        context = testing.DummyResource()
        request = testing.DummyRequest()
        registry = request.registry
        index = 'abc'
        registry.content = DummyContent(index)
        inst = self._makeOne(context, request)
        result = inst.makeindex({'permissions':()}, request.registry)
        self.assertEqual(registry.content.type_name, 'Allowed Index')
        self.assertEqual(result, index)

class TestAddFacetIndexView(unittest.TestCase):
    def setUp(self):
        testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _makeOne(self, context, request):
        from ..catalog import AddFacetIndexView
        return AddFacetIndexView(context, request)

    def test_makeindex(self):
        context = testing.DummyResource()
        request = testing.DummyRequest()
        registry = request.registry
        index = 'abc'
        registry.content = DummyContent(index)
        inst = self._makeOne(context, request)
        result = inst.makeindex({'facets':(), 'name':'name'}, request.registry)
        self.assertEqual(registry.content.type_name, 'Facet Index')
        self.assertEqual(result, index)

class Test_reindex_indexes(unittest.TestCase):
    def setUp(self):
        testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _callFUT(self, context, request):
        from ..catalog import reindex_indexes
        return reindex_indexes(context, request)

    def test_with_indexes(self):
        context = DummyCatalog()
        request = testing.DummyRequest()
        request.mgmt_path = lambda *arg: '/manage'
        request.POST = testing.DummyResource()
        request.POST.getall = {'item-modify':['a']}.get
        result = self._callFUT(context, request)
        self.assertEqual(result.location, '/manage')
        self.assertEqual(
            request.session['_f_success'],
            ['Reindex of selected indexes succeeded'])
        self.assertEqual(context.reindexed, ['a'])

class DummyContent(object):
    def __init__(self, result):
        self.result = result
    def metadata(self, context, name, default=None):
        return self.result
    def create(self, type_name, *arg, **kw):
        self.type_name = type_name
        self.arg = arg
        self.kw = kw
        return self.result
    

class DummyForm(object):
    def render(self, appstruct):
        return 'form'

class DummyLogger(object):
    def exception(self, msg):
        pass
        
class DummyCatalog(object):
    def __init__(self):
        self.objectids = ()

    def reindex(self, indexes=None, registry=None):
        self.indexes = indexes
        self.reindexed = indexes

class DummyIndex(object):
    def __init__(self, parent=None):
        if parent is None:
            parent = DummyCatalog()
        self.__parent__ = parent
        self.__name__ = 'name'

    def indexed_count(self):
        return 1

    def not_indexed_count(self):
        return 1
    
class DummyContentRegistry(object):
    def __init__(self, result):
        self.result = result
        
    def create(self, *arg, **kw):
        return self.result

class DummyResultSet(object):
    def __init__(self, results):
        self.results = results
    def all(self, resolve=False):
        return self.results

class DummyQuery(object):
    def __init__(self, results):
        self.results = results
    def execute(self):
        return DummyResultSet(self.results)

class DummyObjectmap(object):
    def object_for(self, oid):
        return oid
    
