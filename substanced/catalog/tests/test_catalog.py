import re
import unittest
from pyramid import testing

from zope.interface import implementer

from repoze.catalog.interfaces import ICatalogIndex

class TestCatalog(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _makeOne(self, site):
        from .. import Catalog
        return Catalog(site)

    def test_reindex(self):
        from ...interfaces import ICatalogSite
        a = testing.DummyModel()
        self.config.testing_resources({'/a':a})
        L = []
        transaction = DummyTransaction()
        site = testing.DummyModel()
        inst = self._makeOne(site)
        inst.document_map.path_to_docid = {(u'', u'a'): 1}
        self.assertTrue(ICatalogSite.providedBy(site))
        self.assertEqual(site.catalog, inst)
        inst.reindex_doc = lambda docid, model: L.append((docid, model))
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

    def test_reindex_pathre(self):
        from ...interfaces import ICatalogSite
        a = testing.DummyModel()
        b = testing.DummyModel()
        self.config.testing_resources({'/a':a, '/b':b})
        L = []
        site = testing.DummyModel()
        transaction = DummyTransaction()
        inst = self._makeOne(site)
        inst.document_map.path_to_docid = {(u'', u'a'): 1, (u'', u'b'): 2}
        self.assertTrue(ICatalogSite.providedBy(site))
        inst.reindex_doc = lambda docid, model: L.append((docid, model))
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
        from ...interfaces import ICatalogSite
        a = testing.DummyModel()
        b = testing.DummyModel()
        self.config.testing_resources({'/a':a, '/b':b})
        L = []
        site = testing.DummyModel()
        transaction = DummyTransaction()
        inst = self._makeOne(site)
        inst.document_map.path_to_docid = {(u'', u'a'): 1, (u'', u'b'): 2}
        inst.reindex_doc = lambda docid, model: L.append((docid, model))
        out = []
        self.assertTrue(ICatalogSite.providedBy(site))
        inst.reindex(transaction=transaction, dry_run=True, output=out.append)
        self.assertEqual(sorted(L), [(1, a), (2, b)])
        self.assertEqual(out,
                         ['refreshing indexes',
                          'refreshed',
                          '*** aborting ***',
                          'reindexing /b',
                          'reindexing /a',
                          '*** aborting ***'])
        self.assertEqual(transaction.aborted, 2)
        self.assertEqual(transaction.committed, 0)

    def test_it_with_indexes(self):
        a = testing.DummyModel()
        self.config.testing_resources({'/a':a})
        L = []
        site = testing.DummyModel()
        transaction = DummyTransaction()
        inst = self._makeOne(site)
        inst.document_map.path_to_docid = {(u'', u'a'):1}
        index = DummyIndex()
        inst['index'] = index
        self.config.registry._pyramid_catalog_indexes = {'index':index}
        index.reindex_doc = lambda docid, model: L.append((docid, model))
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
        site.catalog = DummyCatalog()
        adapter = self._makeOne(site)
        q = DummyQuery()
        num, docids, resolver = adapter(q)
        self.assertEqual(num, 0)
        self.assertEqual(list(docids), [])

    def test_peachy_keen(self):
        site = self._makeSite()
        site.catalog = DummyCatalog((1, [1]), {1:'/'})
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
        site.catalog = DummyCatalog((1, [1]))
        adapter = self._makeOne(site)
        q = DummyQuery()
        num, docids, resolver = adapter(q)
        self.assertEqual(num, 1)
        self.assertEqual(list(docids), [1])
        results = filter(None, map(resolver, docids))
        self.assertEqual(results, [])

    def test_unfound_docid(self):
        site = self._makeSite()
        site.catalog = DummyCatalog()
        adapter = self._makeOne(site)
        q = DummyQuery()
        num, docids, resolver = adapter(q)
        self.assertEqual(resolver(123), None)

class DummyQuery(object):
    pass    

class DummyDocumentMap(object):
    def __init__(self, docid_to_path=None): 
        if docid_to_path is None:
            docid_to_path = {}
        self.docid_to_path = docid_to_path
        
class DummyCatalog(object):
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
        

@implementer(ICatalogIndex)
class DummyIndex:
    pass


