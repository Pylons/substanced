import re
import unittest
from pyramid import testing

from zope.interface import directlyProvides
from zope.interface import implements

from repoze.catalog.interfaces import ICatalogIndex

class TestCatalogManager(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _makeOne(self, context, output):
        from .. import CatalogManager
        return CatalogManager(context, self.config.registry, output)

    def test_reindex(self):
        from ...interfaces import ICatalogSite
        a = testing.DummyModel()
        self.config.testing_resources({'a':a})
        L = []
        output = L.append
        site = testing.DummyModel()
        site.update_indexes = lambda *arg: L.append('updated')
        catalog = DummyCatalog({'a':1})
        directlyProvides(site, ICatalogSite)
        site.catalog = catalog
        transaction = DummyTransaction()
        inst = self._makeOne(site, output)
        inst.reindex(transaction=transaction)
        self.assertEqual(catalog.reindexed, [1])
        self.assertEqual(L,
                         ['refreshing indexes',
                          'refreshed',
                          '*** committing ***',
                          'reindexing a',
                          '*** committing ***'])
        self.assertEqual(transaction.committed, 2)

    def test_reindex_pathre(self):
        from ...interfaces import ICatalogSite
        a = testing.DummyModel()
        b = testing.DummyModel()
        self.config.testing_resources({'a':a, 'b':b})
        L = []
        output = L.append
        site = testing.DummyModel()
        site.update_indexes = lambda *arg: L.append('updated')
        catalog = DummyCatalog({'a':1, 'b':2})
        directlyProvides(site, ICatalogSite)
        site.catalog = catalog
        transaction = DummyTransaction()
        inst = self._makeOne(site, output)
        inst.reindex(transaction=transaction, path_re=re.compile('a'))
        self.assertEqual(catalog.reindexed, [1])
        self.assertEqual(L,
                         ['refreshing indexes',
                          'refreshed',
                          '*** committing ***',
                          'reindexing a',
                          '*** committing ***'])
        self.assertEqual(transaction.committed, 2)

    def test_reindex_dryrun(self):
        from ...interfaces import ICatalogSite
        a = testing.DummyModel()
        b = testing.DummyModel()
        self.config.testing_resources({'a':a, 'b':b})
        L = []
        output = L.append
        site = testing.DummyModel()
        site.update_indexes = lambda *arg: L.append('updated')
        catalog = DummyCatalog({'a':1, 'b':2})
        directlyProvides(site, ICatalogSite)
        site.catalog = catalog
        transaction = DummyTransaction()
        inst = self._makeOne(site, output)
        inst.reindex(transaction=transaction, dry_run=True)
        self.assertEqual(catalog.reindexed, [1, 2])
        self.assertEqual(L,
                         ['refreshing indexes',
                          'refreshed',
                          '*** aborting ***',
                          'reindexing a',
                          'reindexing b',
                          '*** aborting ***'])
        self.assertEqual(transaction.aborted, 2)
        self.assertEqual(transaction.committed, 0)

    def test_it_with_indexes(self):
        from ...interfaces import ICatalogSite
        a = testing.DummyModel()
        self.config.testing_resources({'a':a})
        L = []
        output = L.append
        site = testing.DummyModel()
        site.update_indexes = lambda *arg: L.append('updated')
        catalog = DummyCatalog({'a':1})
        catalog.index = DummyIndex()
        directlyProvides(site, ICatalogSite)
        site.catalog = catalog
        transaction = DummyTransaction()
        inst = self._makeOne(site, output)
        inst.reindex(transaction=transaction, indexes=('index',))
        self.assertEqual(L,
                         ['refreshing indexes',
                          'refreshed',
                          '*** committing ***',
                          "reindexing only indexes ('index',)",
                          'reindexing a',
                          '*** committing ***'])
        self.assertEqual(transaction.committed, 2)
        self.assertEqual(catalog.index.indexed, {1:a})

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

    def _makeSite(self):
        from ...interfaces import ICatalogSite
        site = testing.DummyModel(__provides__=ICatalogSite)
        return site

    def test_it(self):
        site = self._makeSite()
        site.catalog = DummyCatalog2()
        adapter = self._makeOne(site)
        q = DummyQuery()
        num, docids, resolver = adapter(q)
        self.assertEqual(num, 0)
        self.assertEqual(list(docids), [])

    def test_peachy_keen(self):
        site = self._makeSite()
        site.catalog = DummyCatalog2((1, [1]), {1:'/'})
        ob = object()
        self.config.testing_resources({'/':ob})
        adapter = self._makeOne(site)
        q = DummyQuery()
        num, docids, resolver = adapter(q)
        self.assertEqual(num, 1)
        self.assertEqual(list(docids), [1])
        self.assertEqual(resolver(1), ob)

    def test_unfound_model(self):
        a = testing.DummyModel()
        self.config.testing_resources({'/a':a})
        site = self._makeSite()
        site.catalog = DummyCatalog2((1, [1]))
        adapter = self._makeOne(site)
        q = DummyQuery()
        num, docids, resolver = adapter(q)
        self.assertEqual(num, 1)
        self.assertEqual(list(docids), [1])
        results = filter(None, map(resolver, docids))
        self.assertEqual(results, [])

    def test_unfound_docid(self):
        site = self._makeSite()
        site.catalog = DummyCatalog2()
        adapter = self._makeOne(site)
        q = DummyQuery()
        num, docids, resolver = adapter(q)
        self.assertEqual(resolver(123), None)

class DummyQuery(object):
    pass    

class DummyCache(dict):
    generation = None

class DummyCatalog(object):
    def __init__(self, path_to_docid, indexes=None):
        self.document_map = testing.DummyModel()
        self.document_map.path_to_docid = path_to_docid
        self.indexes = indexes or {}
        self.reindexed = []

    def __getitem__(self, k):
        return getattr(self, k)

    def __iter__(self):
        return iter(self.indexes)

    def reindex_doc(self, docid, model):
        self.reindexed.append(docid)

class DummyDocumentMap(object):
    def __init__(self, docid_to_path=None): 
        if docid_to_path is None:
            docid_to_path = {}
        self.docid_to_path = docid_to_path
        
class DummyCatalog2(object):
    def __init__(self, result=(0, []), docid_to_path=None):
        self.document_map = DummyDocumentMap(docid_to_path)
        self.result = result

    def query(self, q, **kw):
        return self.result

class DummyTransaction(object):
    def __init__(self):
        self.committed = 0
        self.aborted = 0
        
    def commit(self):
        self.committed += 1

    def abort(self):
        self.aborted += 1
        

class DummyIndex:
    implements(ICatalogIndex)
    def __init__(self):
        self.indexed = {}

    def index_doc(self, docid, val):
        self.indexed[docid] = val

    reindex_doc = index_doc



