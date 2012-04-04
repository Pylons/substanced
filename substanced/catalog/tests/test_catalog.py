import re
import unittest
from pyramid import testing

from zope.interface import implementer

from repoze.catalog.interfaces import ICatalogIndex

from ...interfaces import IObjectmapSite, ICatalogSite

class TestCatalog(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _makeOne(self, site):
        from .. import Catalog
        return Catalog(site)

    def test_clear(self):
        site = testing.DummyModel()
        inst = self._makeOne(site)
        inst.objectids.insert(1)
        inst.clear()
        self.assertEqual(list(inst.objectids), [])

    def test_index_doc(self):
        site = testing.DummyModel()
        inst = self._makeOne(site)
        inst.index_doc(1, object())
        self.assertEqual(list(inst.objectids), [1])
        
    def test_unindex_doc_exists(self):
        site = testing.DummyModel()
        inst = self._makeOne(site)
        inst.objectids.insert(1)
        inst.unindex_doc(1)
        self.assertEqual(list(inst.objectids), [])

    def test_unindex_doc_notexists(self):
        site = testing.DummyModel()
        inst = self._makeOne(site)
        inst.unindex_doc(1)
        self.assertEqual(list(inst.objectids), [])

    def test_reindex_doc_exists(self):
        site = testing.DummyModel()
        inst = self._makeOne(site)
        inst.objectids.insert(1)
        inst.reindex_doc(1, object())
        self.assertEqual(list(inst.objectids), [1])
        
    def test_reindex_doc_notexists(self):
        site = testing.DummyModel()
        inst = self._makeOne(site)
        inst.reindex_doc(1, object())
        self.assertEqual(list(inst.objectids), [1])
        
    def test_reindex(self):
        a = testing.DummyModel()
        self.config.testing_resources({'/a':a})
        L = []
        transaction = DummyTransaction()
        site = DummySite()
        site.objectmap.objectid_to_path = {1:(u'', u'a')}
        inst = self._makeOne(site)
        inst.objectids = [1]
        self.assertTrue(ICatalogSite.providedBy(site))
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
        self.config.testing_resources({'/a':a})
        L = []
        transaction = DummyTransaction()
        site = DummySite()
        site.objectmap.objectid_to_path = {1: (u'', u'a'), 2:(u'', u'b')}
        inst = self._makeOne(site)
        inst.objectids = [1, 2]
        self.assertTrue(ICatalogSite.providedBy(site))
        inst.reindex_doc = lambda objectid, model: L.append((objectid, model))
        out = []
        inst.reindex(transaction=transaction, output=out.append)
        self.assertEqual(L, [(1, a)])
        self.assertEqual(out,
                         ['refreshing indexes',
                          'refreshed',
                          '*** committing ***',
                          "reindexing /a",
                          "reindexing /b",
                          "error: /b not found",
                          '*** committing ***'])
        self.assertEqual(transaction.committed, 2)
        
    def test_reindex_pathre(self):
        a = testing.DummyModel()
        b = testing.DummyModel()
        self.config.testing_resources({'/a':a, '/b':b})
        L = []
        site = DummySite()
        site.objectmap.objectid_to_path = {1: (u'', u'a'), 2: (u'', u'b')}
        transaction = DummyTransaction()
        inst = self._makeOne(site)
        inst.objectids = [1, 2]
        self.assertTrue(ICatalogSite.providedBy(site))
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
        self.config.testing_resources({'/a':a, '/b':b})
        L = []
        site = DummySite()
        site.objectmap.objectid_to_path = {1: (u'', u'a'), 2: (u'', u'b')}
        transaction = DummyTransaction()
        inst = self._makeOne(site)
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
        self.config.testing_resources({'/a':a})
        L = []
        site = DummySite()
        site.objectmap.objectid_to_path = {1: (u'', u'a')}
        transaction = DummyTransaction()
        inst = self._makeOne(site)
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
        site = testing.DummyResource()
        inst = self._makeOne(site)
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
        site = testing.DummyResource()
        inst = self._makeOne(site)
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

    def _makeSite(self, objectid_to_path=None):
        site = DummySite(objectid_to_path)
        return site

    def test_query(self):
        site = self._makeSite()
        site.catalog = DummyCatalog()
        adapter = self._makeOne(site)
        q = DummyQuery()
        num, objectids, resolver = adapter.query(q)
        self.assertEqual(num, 0)
        self.assertEqual(list(objectids), [])

    def test_search(self):
        site = self._makeSite()
        site.catalog = DummyCatalog()
        adapter = self._makeOne(site)
        num, objectids, resolver = adapter.search()
        self.assertEqual(num, 0)
        self.assertEqual(list(objectids), [])
        
    def test_query_peachy_keen(self):
        site = self._makeSite({1:(u'',)})
        site.catalog = DummyCatalog((1, [1]))
        ob = object()
        self.config.testing_resources({'/':ob})
        adapter = self._makeOne(site)
        q = DummyQuery()
        num, objectids, resolver = adapter.query(q)
        self.assertEqual(num, 1)
        self.assertEqual(list(objectids), [1])
        self.assertEqual(resolver(1), ob)

    def test_query_unfound_model(self):
        site = self._makeSite({1:(u'', u'a')})
        site.catalog = DummyCatalog((1, [1]))
        adapter = self._makeOne(site)
        q = DummyQuery()
        num, objectids, resolver = adapter.query(q)
        self.assertEqual(num, 1)
        self.assertEqual(list(objectids), [1])
        results = map(resolver, objectids)
        self.assertEqual(results, [None])

    def test_query_unfound_objectid(self):
        site = self._makeSite()
        site.catalog = DummyCatalog()
        adapter = self._makeOne(site)
        q = DummyQuery()
        num, objectids, resolver = adapter.query(q)
        self.assertEqual(resolver(123), None)

class DummyQuery(object):
    pass    

class DummyObjectMap(object):
    def __init__(self, objectid_to_path=None): 
        if objectid_to_path is None:
            objectid_to_path = {}
        self.objectid_to_path = objectid_to_path

    def path_for(self, objectid):
        return self.objectid_to_path.get(objectid)

@implementer(IObjectmapSite, ICatalogSite)
class DummySite(object):
    __parent__ = None
    __name__ = ''
    def __init__(self, objectid_to_path=None):
        self.objectmap = DummyObjectMap(objectid_to_path)
        
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


