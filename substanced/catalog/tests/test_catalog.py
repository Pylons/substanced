import re
import unittest
from pyramid import testing

from zope.interface import (
    implementer,
    alsoProvides,
    )

from repoze.catalog.interfaces import ICatalogIndex

def _makeSite(**kw):
    from ...interfaces import IFolder
    site = testing.DummyResource(__provides__=kw.pop('__provides__', None))
    alsoProvides(site, IFolder)
    services = testing.DummyResource()
    for k, v in kw.items():
        services[k] = v
    site['__services__'] = services
    return site

class TestCatalog(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
        
    def _makeOne(self):
        from .. import Catalog
        return Catalog()

    def test_clear(self):
        inst = self._makeOne()
        inst.objectids.insert(1)
        inst.clear()
        self.assertEqual(list(inst.objectids), [])

    def test_index_doc(self):
        inst = self._makeOne()
        inst.index_doc(1, object())
        self.assertEqual(list(inst.objectids), [1])
        
    def test_unindex_doc_exists(self):
        inst = self._makeOne()
        inst.objectids.insert(1)
        inst.unindex_doc(1)
        self.assertEqual(list(inst.objectids), [])

    def test_unindex_doc_notexists(self):
        inst = self._makeOne()
        inst.unindex_doc(1)
        self.assertEqual(list(inst.objectids), [])

    def test_reindex_doc_exists(self):
        inst = self._makeOne()
        inst.objectids.insert(1)
        inst.reindex_doc(1, object())
        self.assertEqual(list(inst.objectids), [1])
        
    def test_reindex_doc_notexists(self):
        inst = self._makeOne()
        inst.reindex_doc(1, object())
        self.assertEqual(list(inst.objectids), [1])
        
    def test_reindex(self):
        a = testing.DummyModel()
        L = []
        transaction = DummyTransaction()
        inst = self._makeOne()
        objectmap = DummyObjectMap({1:[a, (u'', u'a')]})
        site = _makeSite(catalog=inst, objectmap=objectmap)
        site['a'] = a
        inst.objectids = [1]
        inst.reindex_doc = lambda objectid, model: L.append((objectid, model))
        out = []
        inst.reindex(transaction=transaction, output=out.append)
        self.assertEqual(L, [(1, a)])
        self.assertEqual(out,
                         ['refreshing indexes',
                          'refreshed',
                          '*** committing ***',
                          "reindexing /a",
                          '*** committing ***'])
        self.assertEqual(transaction.committed, 2)

    def test_reindex_with_missing_resource(self):
        a = testing.DummyModel()
        L = []
        transaction = DummyTransaction()
        objectmap = DummyObjectMap(
            {1: [a, (u'', u'a')], 2:[None, (u'', u'b')]}
            )
        inst = self._makeOne()
        site = _makeSite(catalog=inst, objectmap=objectmap)
        site['a'] = a
        inst.objectids = [1, 2]
        inst.reindex_doc = lambda objectid, model: L.append((objectid, model))
        out = []
        inst.reindex(transaction=transaction, output=out.append)
        self.assertEqual(L, [(1, a)])
        self.assertEqual(out,
                         ['refreshing indexes',
                          'refreshed',
                          '*** committing ***',
                          "reindexing /a",
                          "error: object at path /b not found",
                          '*** committing ***'])
        self.assertEqual(transaction.committed, 2)
        
    def test_reindex_pathre(self):
        a = testing.DummyModel()
        b = testing.DummyModel()
        L = []
        objectmap = DummyObjectMap({1: [a, (u'', u'a')], 2: [b, (u'', u'b')]})
        transaction = DummyTransaction()
        inst = self._makeOne()
        site = _makeSite(catalog=inst, objectmap=objectmap)
        site['a'] = a
        site['b'] = b
        inst.objectids = [1, 2]
        inst.reindex_doc = lambda objectid, model: L.append((objectid, model))
        out = []
        inst.reindex(
            transaction=transaction,
            path_re=re.compile('/a'), 
            output=out.append
            )
        self.assertEqual(L, [(1, a)])
        self.assertEqual(out,
                         ['refreshing indexes',
                          'refreshed',
                          '*** committing ***',
                          'reindexing /a',
                          '*** committing ***'])
        self.assertEqual(transaction.committed, 2)

    def test_reindex_dryrun(self):
        a = testing.DummyModel()
        b = testing.DummyModel()
        L = []
        objectmap = DummyObjectMap({1: [a, (u'', u'a')], 2: [b, (u'', u'b')]})
        transaction = DummyTransaction()
        inst = self._makeOne()
        site = _makeSite(catalog=inst, objectmap=objectmap)
        site['a'] = a
        site['b'] = b
        inst.objectids = [1,2]
        inst.reindex_doc = lambda objectid, model: L.append((objectid, model))
        out = []
        inst.reindex(transaction=transaction, dry_run=True, output=out.append)
        self.assertEqual(sorted(L), [(1, a), (2, b)])
        self.assertEqual(out,
                         ['refreshing indexes',
                          'refreshed',
                          '*** aborting ***',
                          'reindexing /a',
                          'reindexing /b',
                          '*** aborting ***'])
        self.assertEqual(transaction.aborted, 2)
        self.assertEqual(transaction.committed, 0)

    def test_reindex_with_indexes(self):
        a = testing.DummyModel()
        L = []
        objectmap = DummyObjectMap({1: [a, (u'', u'a')]})
        transaction = DummyTransaction()
        inst = self._makeOne()
        site = _makeSite(catalog=inst, objectmap=objectmap)
        site['a'] = a
        inst.objectids = [1]
        index = DummyIndex()
        inst['index'] = index
        self.config.registry._substanced_indexes = {'index':index}
        index.reindex_doc = lambda objectid, model: L.append((objectid, model))
        out = []
        inst.reindex(transaction=transaction, indexes=('index',), 
                     output=out.append)
        self.assertEqual(out,
                         ['refreshing indexes',
                          'refreshed',
                          '*** committing ***',
                          "reindexing only indexes ('index',)",
                          'reindexing /a',
                          '*** committing ***'])
        self.assertEqual(transaction.committed, 2)
        self.assertEqual(L, [(1,a)])

    def test_refresh_add_unmentioned(self):
        inst = self._makeOne()
        inst['index'] = DummyIndex()
        registry = testing.DummyResource()
        registry._substanced_indexes = {'index2':DummyIndex(), 
                                        'index':DummyIndex()}
        out = []
        inst.refresh(output=out.append, registry=registry)
        self.assertEqual(out,
                         ['refreshing indexes',
                         'added index2 index',
                         'refreshed'])

    def test_refresh_remove_unmentioned(self):
        inst = self._makeOne()
        inst['index'] = DummyIndex()
        registry = testing.DummyResource()
        registry._substanced_indexes = {}
        out = []
        inst.refresh(output=out.append, registry=registry)
        self.assertEqual(out,
                         ['refreshing indexes',
                         'removed index index',
                         'refreshed'])
        
class TestSearch(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _getTargetClass(self):
        from .. import Search
        return Search

    def _makeOne(self, context):
        adapter = self._getTargetClass()(context)
        return adapter

    def test_query(self):
        catalog = DummyCatalog()
        site = _makeSite(catalog=catalog)
        adapter = self._makeOne(site)
        q = DummyQuery()
        num, objectids, resolver = adapter.query(q)
        self.assertEqual(num, 0)
        self.assertEqual(list(objectids), [])

    def test_search(self):
        catalog = DummyCatalog()
        site = _makeSite(catalog=catalog)
        adapter = self._makeOne(site)
        num, objectids, resolver = adapter.search()
        self.assertEqual(num, 0)
        self.assertEqual(list(objectids), [])
        
    def test_query_peachy_keen(self):
        ob = object()
        objectmap = DummyObjectMap({1:[ob, (u'',)]})
        catalog = DummyCatalog((1, [1]))
        site = _makeSite(objectmap=objectmap, catalog=catalog)
        adapter = self._makeOne(site)
        q = DummyQuery()
        num, objectids, resolver = adapter.query(q)
        self.assertEqual(num, 1)
        self.assertEqual(list(objectids), [1])
        self.assertEqual(resolver(1), ob)

    def test_query_unfound_model(self):
        catalog = DummyCatalog((1, [1]))
        objectmap = DummyObjectMap({1:[None, (u'', u'a')]})
        site = _makeSite(catalog=catalog, objectmap=objectmap)
        adapter = self._makeOne(site)
        q = DummyQuery()
        num, objectids, resolver = adapter.query(q)
        self.assertEqual(num, 1)
        self.assertEqual(list(objectids), [1])
        results = map(resolver, objectids)
        self.assertEqual(results, [None])

    def test_query_unfound_objectid(self):
        catalog = DummyCatalog()
        objectmap = DummyObjectMap({})
        site = _makeSite(catalog=catalog, objectmap=objectmap)
        adapter = self._makeOne(site)
        q = DummyQuery()
        num, objectids, resolver = adapter.query(q)
        self.assertEqual(resolver(123), None)

class Test_query_catalog(unittest.TestCase):
    def _makeOne(self, request):
        from .. import query_catalog
        return query_catalog(request)

    def test_it(self):
        request = testing.DummyRequest()
        request.context = testing.DummyResource()
        inst = self._makeOne(request)
        inst.Search = DummySearch(True)
        result = inst('q', a=1)
        self.assertEqual(result, True)

class Test_search_catalog(unittest.TestCase):
    def _makeOne(self, request):
        from .. import search_catalog
        return search_catalog(request)

    def test_it(self):
        request = testing.DummyRequest()
        request.context = testing.DummyResource()
        inst = self._makeOne(request)
        inst.Search = DummySearch(True)
        result = inst(a=1)
        self.assertEqual(result, True)
        
class DummySearch(object):
    def __init__(self, result):
        self.result = result

    def __call__(self, context):
        return self

    def query(self, *arg, **kw):
        return self.result

    def search(self, **kw):
        return self.result

class DummyQuery(object):
    pass    

class DummyObjectMap(object):
    def __init__(self, objectid_to=None): 
        if objectid_to is None:
            objectid_to = {}
        self.objectid_to = objectid_to

    def path_for(self, objectid):
        data = self.objectid_to.get(objectid)
        if data is None:
            return
        return data[1]

    def object_for(self, objectid):
        data = self.objectid_to.get(objectid)
        if data is None:
            return
        return data[0]

class DummyCatalog(object):
    def __init__(self, result=(0, [])):
        self.result = result

    def query(self, q, **kw):
        return self.result

    def search(self, **kw):
        return self.result

class DummyTransaction(object):
    def __init__(self):
        self.committed = 0
        self.aborted = 0
        
    def commit(self):
        self.committed += 1

    def abort(self):
        self.aborted += 1
        

@implementer(ICatalogIndex)
class DummyIndex:
    pass


