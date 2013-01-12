import unittest
from pyramid import testing

class TestSearchViews(unittest.TestCase):
    def _makeOne(self, context, request):
        from ..search import SearchViews
        return SearchViews(context, request)

    def _makeRequest(self, **kw):
        request = testing.DummyRequest()
        request.sdiapi = DummySDIAPI()
        return request

    def _makeCatalogs(self, oids=(), resources=()):
        catalogs = DummyCatalogs()
        catalog = DummyCatalog(oids, resources)
        catalogs['system'] = catalog
        return catalogs

    def test_search_no_results(self):
        from substanced.interfaces import IFolder
        context = testing.DummyResource(__provides__=IFolder)
        request = self._makeRequest()
        request.params['query'] = 'abc'
        context['catalogs'] = self._makeCatalogs()
        result = testing.DummyResource()
        result.__name__ = 'abcde'
        context.__objectmap__ = DummyObjectMap(result)
        inst = self._makeOne(context, request)
        results = inst.search()
        self.assertEqual(results, [])

    def test_search_results_resource_with_title(self):
        from substanced.interfaces import IFolder
        context = testing.DummyResource(__provides__=IFolder)
        request = self._makeRequest()
        request.params['query'] = 'abc'
        result = testing.DummyResource()
        result.title = 'Some Resource'
        context.__objectmap__ = DummyObjectMap(result)
        context['catalogs'] = self._makeCatalogs(oids=[1],
                                                 resources=(result,))
        inst = self._makeOne(context, request)
        results = inst.search()
        self.assertEqual(len(results), 1)
        item = results[0]
        self.assertEqual(item['label'], 'Some Resource')
        self.assertEqual(item['url'], '/mgmt_path')

    def test_search_results_resource_no_title(self):
        from substanced.interfaces import IFolder
        context = testing.DummyResource(__provides__=IFolder)
        request = self._makeRequest()
        request.params['query'] = 'abc'
        result = testing.DummyResource()
        result.__name__ = 'abcde'
        context.__objectmap__ = DummyObjectMap(result)
        context['catalogs'] = self._makeCatalogs(oids=[1],
                                                 resources=(result,))
        inst = self._makeOne(context, request)
        results = inst.search()
        self.assertEqual(len(results), 1)
        item = results[0]
        self.assertEqual(item['label'], 'abcde')
        self.assertEqual(item['url'], '/mgmt_path')

class DummyCatalogs(testing.DummyResource):
    __is_service__ = True

class DummyCatalog(object):
    def __init__(self, result=(), resources=()):
        self.result = DummyResultSet(result, resources)

    def __getitem__(self, name):
        return DummyIndex(self.result)

class DummyResultSet(object):
    def __init__(self, result, resources):
        self.ids = result
        self.resources = resources

    def sort(self, *arg, **kw):
        return self

    def __len__(self):
        return len(self.ids)

    def resolver(self, oid):
        return self.resources[0]

class DummyIndex(object):
    def __init__(self, result):
        self.result = result

    def execute(self):
        return self.result
        
    def eq(self, *arg, **kw):
        return self

    def allows(self, *arg, **kw):
        return self

    def __and__(self, other):
        return self
    
class DummyObjectMap(object):
    def __init__(self, result):
        self.result = result
    def object_for(self, oid):
        return self.result

class DummySDIAPI(object):
    def mgmt_path(self, *arg, **kw):
        return '/mgmt_path'
