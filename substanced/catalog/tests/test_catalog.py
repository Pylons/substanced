import re
import unittest
from pyramid import testing
import BTrees

from zope.interface import (
    implementer,
    alsoProvides,
    )

from hypatia.interfaces import IIndex

def _makeSite(**kw):
    from ...interfaces import IFolder
    site = testing.DummyResource(__provides__=kw.pop('__provides__', None))
    alsoProvides(site, IFolder)
    services = testing.DummyResource()
    objectmap = kw.pop('objectmap', None)
    if objectmap is not None:
        site.__objectmap__ = objectmap
    for k, v in kw.items():
        services[k] = v
    site['__services__'] = services
    return site

class TestCatalog(unittest.TestCase):
    family = BTrees.family64
    
    def setUp(self):
        self.config = testing.setUp()
        self.config.registry.content = DummyContentRegistry()

    def tearDown(self):
        testing.tearDown()

    def _getTargetClass(self):
        from .. import Catalog
        return Catalog
        
    def _makeOne(self, *arg, **kw):
        cls = self._getTargetClass()
        return cls(*arg, **kw)

    def test___sd_addable__True(self):
        inst = self._makeOne()
        intr = {'meta':{'is_index':True}}
        self.assertTrue(inst.__sd_addable__(intr))

    def test___sd_addable__False(self):
        inst = self._makeOne()
        intr = {'meta':{}}
        self.assertFalse(inst.__sd_addable__(intr))

    def test_klass_provides_ICatalog(self):
        klass = self._getTargetClass()
        from zope.interface.verify import verifyClass
        from ...interfaces import ICatalog
        verifyClass(ICatalog, klass)
        
    def test_inst_provides_ICatalog(self):
        from zope.interface.verify import verifyObject
        from ...interfaces import ICatalog
        inst = self._makeOne()
        verifyObject(ICatalog, inst)

    def test_reset(self):
        catalog = self._makeOne()
        idx = DummyIndex()
        catalog['name'] = idx
        catalog.reset()
        self.assertEqual(idx.cleared, True)
        
    def test_reset_objectids(self):
        inst = self._makeOne()
        inst.objectids.insert(1)
        inst.reset()
        self.assertEqual(list(inst.objectids), [])

    def test_ctor_defaults(self):
        catalog = self._makeOne()
        self.failUnless(catalog.family is self.family)

    def test_ctor_explicit_family(self):
        catalog = self._makeOne(family=BTrees.family32)
        self.failUnless(catalog.family is BTrees.family32)

    def test_index_doc_indexes(self):
        catalog = self._makeOne()
        idx = DummyIndex()
        catalog['name'] = idx
        catalog.index_doc(1, 'value')
        self.assertEqual(idx.docid, 1)
        self.assertEqual(idx.value, 'value')

    def test_index_doc_objectids(self):
        inst = self._makeOne()
        inst.index_doc(1, object())
        self.assertEqual(list(inst.objectids), [1])

    def test_index_doc_nonint_docid(self):
        catalog = self._makeOne()
        idx = DummyIndex()
        catalog['name'] = idx
        self.assertRaises(ValueError, catalog.index_doc, 'abc', 'value')

    def test_unindex_doc_indexes(self):
        catalog = self._makeOne()
        idx = DummyIndex()
        catalog['name'] = idx
        catalog.unindex_doc(1)
        self.assertEqual(idx.unindexed, 1)
        
    def test_unindex_doc_objectids_exists(self):
        inst = self._makeOne()
        inst.objectids.insert(1)
        inst.unindex_doc(1)
        self.assertEqual(list(inst.objectids), [])

    def test_unindex_doc_objectids_notexists(self):
        inst = self._makeOne()
        inst.unindex_doc(1)
        self.assertEqual(list(inst.objectids), [])

    def test_reindex_doc_indexes(self):
        catalog = self._makeOne()
        idx = DummyIndex()
        catalog['name'] = idx
        catalog.reindex_doc(1, 'value')
        self.assertEqual(idx.reindexed_docid, 1)
        self.assertEqual(idx.reindexed_ob, 'value')

    def test_reindex_doc_objectids_exists(self):
        inst = self._makeOne()
        inst.objectids.insert(1)
        inst.reindex_doc(1, object())
        self.assertEqual(list(inst.objectids), [1])
        
    def test_reindex_doc_objectids_notexists(self):
        inst = self._makeOne()
        inst.reindex_doc(1, object())
        self.assertEqual(list(inst.objectids), [1])
        
    def test_reindex(self):
        a = testing.DummyModel()
        L = []
        transaction = DummyTransaction()
        inst = self._makeOne()
        inst.transaction = transaction
        objectmap = DummyObjectMap({1:[a, (u'', u'a')]})
        site = _makeSite(catalog=inst, objectmap=objectmap)
        site['a'] = a
        inst.objectids = [1]
        inst.reindex_doc = lambda objectid, model: L.append((objectid, model))
        out = []
        inst.reindex(output=out.append)
        self.assertEqual(len(L), 1)
        self.assertEqual(L[0][0], 1)
        self.assertEqual(L[0][1].content, a)
        self.assertEqual(out,
                          ["reindexing /a",
                          '*** committing ***'])
        self.assertEqual(transaction.committed, 1)

    def test_reindex_with_missing_path(self):
        a = testing.DummyModel()
        L = []
        transaction = DummyTransaction()
        objectmap = DummyObjectMap(
            {1: [a, (u'', u'a')], 2:[None, (u'', u'b')]}
            )
        inst = self._makeOne()
        inst.transaction = transaction
        site = _makeSite(catalog=inst, objectmap=objectmap)
        site['a'] = a
        inst.objectids = [1, 2]
        inst.reindex_doc = lambda objectid, model: L.append((objectid, model))
        out = []
        inst.reindex(output=out.append)
        self.assertEqual(L[0][0], 1)
        self.assertEqual(L[0][1].content, a)
        self.assertEqual(out,
                          ["reindexing /a",
                          "error: object at path /b not found",
                          '*** committing ***'])
        self.assertEqual(transaction.committed, 1)

    def test_reindex_with_missing_objectid(self):
        a = testing.DummyModel()
        L = []
        transaction = DummyTransaction()
        objectmap = DummyObjectMap()
        inst = self._makeOne()
        inst.transaction = transaction
        site = _makeSite(catalog=inst, objectmap=objectmap)
        site['a'] = a
        inst.objectids = [1]
        out = []
        inst.reindex(output=out.append)
        self.assertEqual(L, [])
        self.assertEqual(out,
                          ["error: no path for objectid 1 in object map",
                          '*** committing ***'])
        self.assertEqual(transaction.committed, 1)
        
        
    def test_reindex_pathre(self):
        a = testing.DummyModel()
        b = testing.DummyModel()
        L = []
        objectmap = DummyObjectMap({1: [a, (u'', u'a')], 2: [b, (u'', u'b')]})
        transaction = DummyTransaction()
        inst = self._makeOne()
        inst.transaction = transaction
        site = _makeSite(catalog=inst, objectmap=objectmap)
        site['a'] = a
        site['b'] = b
        inst.objectids = [1, 2]
        inst.reindex_doc = lambda objectid, model: L.append((objectid, model))
        out = []
        inst.reindex(
            path_re=re.compile('/a'), 
            output=out.append
            )
        self.assertEqual(L[0][0], 1)
        self.assertEqual(L[0][1].content, a)
        self.assertEqual(out,
                          ['reindexing /a',
                          '*** committing ***'])
        self.assertEqual(transaction.committed, 1)

    def test_reindex_dryrun(self):
        a = testing.DummyModel()
        b = testing.DummyModel()
        L = []
        objectmap = DummyObjectMap({1: [a, (u'', u'a')], 2: [b, (u'', u'b')]})
        transaction = DummyTransaction()
        inst = self._makeOne()
        inst.transaction = transaction
        site = _makeSite(catalog=inst, objectmap=objectmap)
        site['a'] = a
        site['b'] = b
        inst.objectids = [1,2]
        inst.reindex_doc = lambda objectid, model: L.append((objectid, model))
        out = []
        inst.reindex(dry_run=True, output=out.append)
        self.assertEqual(len(L), 2)
        L.sort()
        self.assertEqual(L[0][0], 1)
        self.assertEqual(L[0][1].content, a)
        self.assertEqual(L[1][0], 2)
        self.assertEqual(L[1][1].content, b)
        self.assertEqual(out,
                         ['reindexing /a',
                          'reindexing /b',
                          '*** aborting ***'])
        self.assertEqual(transaction.aborted, 1)
        self.assertEqual(transaction.committed, 0)

    def test_reindex_with_indexes(self):
        a = testing.DummyModel()
        L = []
        objectmap = DummyObjectMap({1: [a, (u'', u'a')]})
        transaction = DummyTransaction()
        inst = self._makeOne()
        inst.transaction = transaction
        site = _makeSite(catalog=inst, objectmap=objectmap)
        site['a'] = a
        inst.objectids = [1]
        index = DummyIndex()
        inst['index'] = index
        self.config.registry._substanced_indexes = {'index':index}
        index.reindex_doc = lambda objectid, model: L.append((objectid, model))
        out = []
        inst.reindex(indexes=('index',),  output=out.append)
        self.assertEqual(out,
                          ["reindexing only indexes ('index',)",
                          'reindexing /a',
                          '*** committing ***'])
        self.assertEqual(transaction.committed, 1)
        self.assertEqual(len(L), 1)
        self.assertEqual(L[0][0], 1)
        self.assertEqual(L[0][1].content, a)

    def test_update_indexes_nothing_to_do(self):
        registry = self.config.registry
        out = []
        inst = self._makeOne()
        transaction = DummyTransaction()
        inst.transaction = transaction
        inst.update_indexes('system', registry=registry,  output=out.append)
        self.assertEqual(out,  
            ["update_indexes: starting category 'system'", 
             'update_indexes: no indexes added or removed', 
             "update_indexes: finished with category 'system'"])
        self.assertEqual(transaction.committed, 0)
        self.assertEqual(transaction.aborted, 0)

    def _setup_index(self):
        registry = self.config.registry
        from .. import get_candidate_indexes, get_index_factories
        categories = get_candidate_indexes(registry)
        idx = {'factory_name':'field', 'factory_args':{}}
        categories['system'] = {'name':idx}
        factories = get_index_factories(registry)
        dummyidx = testing.DummyModel()
        factories['field'] = lambda *arg, **kw: dummyidx

    def test_update_indexes_add_single(self):
        self._setup_index()
        registry = self.config.registry
        out = []
        inst = self._makeOne()
        transaction = DummyTransaction()
        inst.transaction = transaction
        inst.update_indexes('system', registry=registry,  output=out.append)
        self.assertEqual(out,  
            ["update_indexes: starting category 'system'", 
            "update_indexes: adding field index named 'name'",
            '*** committing ***',
            'update_indexes: not reindexing added indexes',
             "update_indexes: finished with category 'system'"])
        self.assertEqual(transaction.committed, 1)
        self.assertEqual(transaction.aborted, 0)
        self.assertTrue('name' in inst)

    def test_update_indexes_add_single_dryrun_with_reindex(self):
        registry = self.config.registry
        self._setup_index()
        out = []
        inst = self._makeOne()
        transaction = DummyTransaction()
        inst.transaction = transaction
        inst.update_indexes('system', registry=registry,  output=out.append,
            dry_run=True, reindex=True)
        self.assertEqual(out,  
            ["update_indexes: starting category 'system'", 
            "update_indexes: adding field index named 'name'",
            '*** aborting ***',
            'update_indexes: reindexing added indexes',
            "reindexing only indexes ['name']",
            '*** aborting ***',
             "update_indexes: finished with category 'system'"])
        self.assertEqual(transaction.committed, 0)
        self.assertEqual(transaction.aborted, 2)
        self.assertTrue('name' in inst)


    def test_update_indexes_add_single_already_exists(self):
        self._setup_index()
        registry = self.config.registry
        out = []
        inst = self._makeOne()
        existing = testing.DummyResource()
        existing.sd_category = 'notsystem'
        inst['name'] = existing
        transaction = DummyTransaction()
        inst.transaction = transaction
        inst.update_indexes('system', registry=registry,  output=out.append)
        self.assertEqual(out,  
            ["update_indexes: starting category 'system'", 
            "update_indexes: not replacing existing index in category "
            "'notsystem' named 'name'",
             'update_indexes: no indexes added or removed', 
             "update_indexes: finished with category 'system'"])
        self.assertEqual(transaction.committed, 0)
        self.assertEqual(transaction.aborted, 0)
        self.assertEqual(inst['name'], existing)

    def test_update_indexes_add_single_already_exists_replace(self):
        self._setup_index()
        registry = self.config.registry
        out = []
        inst = self._makeOne()
        existing = testing.DummyResource()
        existing.sd_category = 'notsystem'
        inst['name'] = existing
        transaction = DummyTransaction()
        inst.transaction = transaction
        inst.update_indexes('system', registry=registry,  output=out.append,
            replace=True)
        self.assertEqual(out,  
            ["update_indexes: starting category 'system'", 
            "update_indexes: replacing existing index in category "
            "'notsystem' named 'name'",
            "update_indexes: adding field index named 'name'",
            '*** committing ***',
            'update_indexes: not reindexing added indexes',
            "update_indexes: finished with category 'system'"]
            )
        self.assertEqual(transaction.committed, 1)
        self.assertEqual(transaction.aborted, 0)
        self.assertNotEqual(inst['name'], existing)

    def test_update_indexes_remove_single(self):
        self._setup_index()
        registry = self.config.registry
        out = []
        inst = self._makeOne()
        transaction = DummyTransaction()
        inst.transaction = transaction
        existing = testing.DummyModel()
        existing.sd_category = 'system'
        inst['other'] = existing
        inst.update_indexes('system', registry=registry,  output=out.append)
        self.assertEqual(out,  
            ["update_indexes: starting category 'system'", 
            "update_indexes: adding field index named 'name'",
            "update_indexes: removing index named u'other'",
            '*** committing ***',
            'update_indexes: not reindexing added indexes',
            "update_indexes: finished with category 'system'"])
        self.assertEqual(transaction.committed, 1)
        self.assertEqual(transaction.aborted, 0)
        self.assertTrue('name' in inst)

    def test_update_indexes_remove_diffcat(self):
        self._setup_index()
        registry = self.config.registry
        out = []
        inst = self._makeOne()
        transaction = DummyTransaction()
        inst.transaction = transaction
        existing = testing.DummyModel()
        existing.sd_category = 'notsystem'
        inst['other'] = existing
        inst.update_indexes('system', registry=registry,  output=out.append)
        self.assertEqual(out,  
            ["update_indexes: starting category 'system'", 
            "update_indexes: adding field index named 'name'",
            '*** committing ***',
            'update_indexes: not reindexing added indexes',
             "update_indexes: finished with category 'system'"])
        self.assertEqual(transaction.committed, 1)
        self.assertEqual(transaction.aborted, 0)
        self.assertTrue('name' in inst)
    
class TestSearch(unittest.TestCase):
    family = BTrees.family64
    
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _getTargetClass(self):
        from .. import Search
        return Search

    def _makeOne(self, context, permission_checker=None):
        adapter = self._getTargetClass()(context, permission_checker)
        return adapter

    def test_query(self):
        catalog = DummyCatalog()
        site = _makeSite(catalog=catalog)
        adapter = self._makeOne(site)
        adapter.CatalogQuery = DummyCatalogQuery()
        q = DummyQuery()
        num, objectids, resolver = adapter.query(q)
        self.assertEqual(num, 0)
        self.assertEqual(list(objectids), [])

    def test_search(self):
        catalog = DummyCatalog()
        site = _makeSite(catalog=catalog)
        adapter = self._makeOne(site)
        adapter.CatalogQuery = DummyCatalogQuery()
        num, objectids, resolver = adapter.search()
        self.assertEqual(num, 0)
        self.assertEqual(list(objectids), [])
        
    def test_sort(self):
        catalog = DummyCatalog()
        site = _makeSite(catalog=catalog)
        adapter = self._makeOne(site)
        adapter.CatalogQuery = DummyCatalogQuery()
        docids = self.family.IF.Set([1,2,3])
        num, objectids, resolver = adapter.sort(docids, 'name')
        self.assertEqual(num, 0)
        self.assertEqual(list(objectids), [])
        
    def test_sort_with_permission_checker_returns_true(self):
        ob = object()
        objectmap = DummyObjectMap({1:[ob, (u'',)]})
        catalog = DummyCatalog()
        site = _makeSite(objectmap=objectmap, catalog=catalog)
        def permitted(ob):
            return True
        adapter = self._makeOne(site, permitted)
        docids = self.family.IF.Set([1])
        adapter.CatalogQuery = DummyCatalogQuery((1, docids))
        num, objectids, resolver = adapter.sort(docids, 'name')
        self.assertEqual(num, 1)
        self.assertEqual(list(objectids), [1])
        self.assertEqual(resolver(1), ob)
        
    def test_query_peachy_keen(self):
        ob = object()
        objectmap = DummyObjectMap({1:[ob, (u'',)]})
        catalog = DummyCatalog()
        site = _makeSite(objectmap=objectmap, catalog=catalog)
        adapter = self._makeOne(site)
        adapter.CatalogQuery = DummyCatalogQuery((1, [1]))
        q = DummyQuery()
        num, objectids, resolver = adapter.query(q)
        self.assertEqual(num, 1)
        self.assertEqual(list(objectids), [1])
        self.assertEqual(resolver(1), ob)

    def test_query_unfound_model(self):
        catalog = DummyCatalog()
        objectmap = DummyObjectMap({1:[None, (u'', u'a')]})
        site = _makeSite(catalog=catalog, objectmap=objectmap)
        adapter = self._makeOne(site)
        adapter.CatalogQuery = DummyCatalogQuery((1, [1]))
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
        adapter.CatalogQuery = DummyCatalogQuery()
        q = DummyQuery()
        num, objectids, resolver = adapter.query(q)
        self.assertEqual(resolver(123), None)

    def test_query_with_permission_checker_returns_true(self):
        ob = object()
        objectmap = DummyObjectMap({1:[ob, (u'',)]})
        catalog = DummyCatalog()
        site = _makeSite(objectmap=objectmap, catalog=catalog)
        def permitted(ob):
            return True
        adapter = self._makeOne(site, permitted)
        adapter.CatalogQuery = DummyCatalogQuery((1, [1]))
        q = DummyQuery()
        num, objectids, resolver = adapter.query(q)
        self.assertEqual(num, 1)
        self.assertEqual(list(objectids), [1])
        self.assertEqual(resolver(1), ob)

    def test_query_with_permission_checker_returns_false(self):
        ob = object()
        objectmap = DummyObjectMap({1:[ob, (u'',)]})
        catalog = DummyCatalog()
        site = _makeSite(objectmap=objectmap, catalog=catalog)
        def permitted(ob):
            return False
        adapter = self._makeOne(site, permitted)
        adapter.CatalogQuery = DummyCatalogQuery((1, [1]))
        q = DummyQuery()
        num, objectids, resolver = adapter.query(q)
        self.assertEqual(num, 0)
        self.assertEqual(list(objectids), [])
        
    def test_query_with_permission_checker_unfound_model(self):
        catalog = DummyCatalog()
        objectmap = DummyObjectMap({1:[None, (u'', u'a')]})
        site = _makeSite(catalog=catalog, objectmap=objectmap)
        def permitted(ob): return True
        adapter = self._makeOne(site, permitted)
        adapter.CatalogQuery = DummyCatalogQuery((1, [1]))
        q = DummyQuery()
        num, objectids, resolver = adapter.query(q)
        self.assertEqual(num, 0)
        self.assertEqual(list(objectids), [])

    def test_search_with_permission_checker_returns_true(self):
        ob = object()
        objectmap = DummyObjectMap({1:[ob, (u'',)]})
        catalog = DummyCatalog()
        site = _makeSite(objectmap=objectmap, catalog=catalog)
        def permitted(ob):
            return True
        adapter = self._makeOne(site, permitted)
        adapter.CatalogQuery = DummyCatalogQuery((1, [1]))
        num, objectids, resolver = adapter.search()
        self.assertEqual(num, 1)
        self.assertEqual(list(objectids), [1])
        self.assertEqual(resolver(1), ob)

    def test_search_with_permission_checker_returns_false(self):
        ob = object()
        objectmap = DummyObjectMap({1:[ob, (u'',)]})
        catalog = DummyCatalog()
        site = _makeSite(objectmap=objectmap, catalog=catalog)
        def permitted(ob):
            return False
        adapter = self._makeOne(site, permitted)
        adapter.CatalogQuery = DummyCatalogQuery((1, [1]))
        num, objectids, resolver = adapter.search()
        self.assertEqual(num, 0)
        self.assertEqual(list(objectids), [])
        
    def test_search_with_permission_checker_unfound_model(self):
        catalog = DummyCatalog()
        objectmap = DummyObjectMap({1:[None, (u'', u'a')]})
        site = _makeSite(catalog=catalog, objectmap=objectmap)
        def permitted(ob): return True
        adapter = self._makeOne(site, permitted)
        adapter.CatalogQuery = DummyCatalogQuery((1, [1]))
        num, objectids, resolver = adapter.search()
        self.assertEqual(num, 0)
        self.assertEqual(list(objectids), [])

class TestSearchFunctional(unittest.TestCase):
    family = BTrees.family64
    
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _getTargetClass(self):
        from .. import Search
        return Search
    
    def _makeOne(self, context, permission_checker=None, family=None):
        adapter = self._getTargetClass()(context, permission_checker,
                                         family=self.family)
        return adapter
    
    def test_search(self):
        objectmap = DummyObjectMap()
        catalog = DummyCatalog()
        site = _makeSite(objectmap=objectmap, catalog=catalog)
        IFSet = self.family.IF.Set
        adapter = self._makeOne(site)
        c1 = IFSet([1, 2, 3])
        idx1 = DummyIndex(c1)
        catalog['name1'] = idx1
        c2 = IFSet([3, 4, 5])
        idx2 = DummyIndex(c2)
        catalog['name2'] = idx2
        numdocs, result, resolver = adapter.search(name1={}, name2={})
        self.assertEqual(numdocs, 1)
        self.assertEqual(list(result), [3])

    def test_search_index_returns_empty(self):
        IFSet = self.family.IF.Set
        objectmap = DummyObjectMap()
        catalog = DummyCatalog()
        site = _makeSite(objectmap=objectmap, catalog=catalog)
        adapter = self._makeOne(site)
        c1 = IFSet([])
        idx1 = DummyIndex(c1)
        catalog['name1'] = idx1
        c2 = IFSet([3, 4, 5])
        idx2 = DummyIndex(c2)
        catalog['name2'] = idx2
        numdocs, result, resolver = adapter.search(name1={}, name2={})
        self.assertEqual(numdocs, 0)
        self.assertEqual(list(result), [])

    def test_search_no_intersection(self):
        IFSet = self.family.IF.Set
        objectmap = DummyObjectMap()
        catalog = DummyCatalog()
        site = _makeSite(objectmap=objectmap, catalog=catalog)
        adapter = self._makeOne(site)
        c1 = IFSet([1, 2])
        idx1 = DummyIndex(c1)
        catalog['name1'] = idx1
        c2 = IFSet([3, 4, 5])
        idx2 = DummyIndex(c2)
        catalog['name2'] = idx2
        numdocs, result, resolver = adapter.search(name1={}, name2={})
        self.assertEqual(numdocs, 0)
        self.assertEqual(list(result), [])

    def test_search_index_query_order_returns_empty(self):
        IFSet = self.family.IF.Set
        objectmap = DummyObjectMap()
        catalog = DummyCatalog()
        site = _makeSite(objectmap=objectmap, catalog=catalog)
        adapter = self._makeOne(site)
        c1 = IFSet([1, 2])
        idx1 = DummyIndex(c1)
        catalog['name1'] = idx1
        c2 = IFSet([])
        idx2 = DummyIndex(c2)
        catalog['name2'] = idx2
        numdocs, result, resolver = adapter.search(
            name1={},
            name2={},
            index_query_order=['name2', 'name1']
            )
        self.assertEqual(numdocs, 0)
        self.assertEqual(list(result), [])

    def test_search_no_indexes_in_search(self):
        objectmap = DummyObjectMap()
        catalog = DummyCatalog()
        site = _makeSite(objectmap=objectmap, catalog=catalog)
        adapter = self._makeOne(site)
        numdocs, result, resolver = adapter.search()
        self.assertEqual(numdocs, 0)
        self.assertEqual(list(result), [])

    def test_search_noindex(self):
        objectmap = DummyObjectMap()
        catalog = DummyCatalog()
        site = _makeSite(objectmap=objectmap, catalog=catalog)
        adapter = self._makeOne(site)
        self.assertRaises(ValueError, adapter.search, name1={})

    def test_search_noindex_ordered(self):
        objectmap = DummyObjectMap()
        catalog = DummyCatalog()
        site = _makeSite(objectmap=objectmap, catalog=catalog)
        adapter = self._makeOne(site)
        self.assertRaises(ValueError, adapter.search, name1={},
                          index_query_order=['name1'])

    def test_search_with_sortindex_ascending(self):
        IFSet = self.family.IF.Set
        objectmap = DummyObjectMap()
        catalog = DummyCatalog()
        site = _makeSite(objectmap=objectmap, catalog=catalog)
        adapter = self._makeOne(site)
        c1 = IFSet([1, 2, 3, 4, 5])
        idx1 = DummyIndex(c1)
        catalog['name1'] = idx1
        c2 = IFSet([3, 4, 5])
        idx2 = DummyIndex(c2)
        catalog['name2'] = idx2
        numdocs, result, resolver = adapter.search(
            name1={}, name2={}, sort_index='name1')
        self.assertEqual(numdocs, 3)
        self.assertEqual(list(result), ['sorted1', 'sorted2', 'sorted3'])

    def test_search_with_sortindex_reverse(self):
        IFSet = self.family.IF.Set
        objectmap = DummyObjectMap()
        catalog = DummyCatalog()
        site = _makeSite(objectmap=objectmap, catalog=catalog)
        adapter = self._makeOne(site)
        c1 = IFSet([1, 2, 3, 4, 5])
        idx1 = DummyIndex(c1)
        catalog['name1'] = idx1
        c2 = IFSet([3, 4, 5])
        idx2 = DummyIndex(c2)
        catalog['name2'] = idx2
        numdocs, result, resolver = adapter.search(
            name1={}, name2={}, sort_index='name1',
            reverse=True)
        self.assertEqual(numdocs, 3)
        self.assertEqual(list(result), ['sorted3', 'sorted2', 'sorted1'])

    def test_search_with_sort_type(self):
        IFSet = self.family.IF.Set
        objectmap = DummyObjectMap()
        catalog = DummyCatalog()
        site = _makeSite(objectmap=objectmap, catalog=catalog)
        adapter = self._makeOne(site)
        c1 = IFSet([1, 2, 3, 4, 5])
        idx1 = DummyIndex(c1)
        catalog['name1'] = idx1
        fwscan = object()
        numdocs, result, resolver = adapter.search(
            name1={},
            sort_index='name1',
            limit=1,
            sort_type=fwscan
            )
        self.assertEqual(idx1.sort_type, fwscan)

    def test_search_limited(self):
        IFSet = self.family.IF.Set
        objectmap = DummyObjectMap()
        catalog = DummyCatalog()
        site = _makeSite(objectmap=objectmap, catalog=catalog)
        adapter = self._makeOne(site)
        c1 = IFSet([1, 2, 3, 4, 5])
        idx1 = DummyIndex(c1)
        catalog['name1'] = idx1
        numdocs, result, resolver = adapter.search(
            name1={}, sort_index='name1', limit=1
            )
        self.assertEqual(numdocs, 1)
        self.assertEqual(idx1.limit, 1)

    def _test_functional_merge(self, **extra):
        objectmap = DummyObjectMap()
        catalog = DummyCatalog()
        site = _makeSite(objectmap=objectmap, catalog=catalog)
        adapter = self._makeOne(site)
        from ..indexes import FieldIndex
        from ..indexes import KeywordIndex
        from ..indexes import TextIndex
        class Content(object):
            def __init__(self, field, keyword, text):
                self.field = field
                self.keyword = keyword
                self.text = text
        field = FieldIndex('field')
        keyword = KeywordIndex('keyword')
        text = TextIndex('text')
        catalog['field'] = field
        catalog['keyword'] = keyword
        catalog['text'] = text
        map = {
            1:Content('field1', ['keyword1', 'same'], 'text one'),
            2:Content('field2', ['keyword2', 'same'], 'text two'),
            3:Content('field3', ['keyword3', 'same'], 'text three'),
            }
        for num, doc in map.items():
            for idx in catalog.values():
                idx.index_doc(num, doc)
        num, result, resolver = adapter.search(
            field=('field1', 'field1'), **extra)
        self.assertEqual(num, 1)
        self.assertEqual(list(result), [1])
        num, result, resolver = adapter.search(
            field=('field2', 'field2'), **extra)
        self.assertEqual(num, 1)
        self.assertEqual(list(result), [2])
        num, result, resolver = adapter.search(field=('field2', 'field2'),
                                               keyword='keyword2', **extra)
        self.assertEqual(num, 1)
        self.assertEqual(list(result), [2])
        num, result, resolver = adapter.search(
            field=('field2', 'field2'), text='two',
            **extra)
        self.assertEqual(num, 1)
        self.assertEqual(list(result), [2])
        num, result, resolver = adapter.search(
            text='text', keyword='same', **extra)
        self.assertEqual(num, 3)
        self.assertEqual(list(result), [1,2,3])

    def test_functional_index_merge_unordered(self):
        return self._test_functional_merge()

    def test_functional_index_merge_ordered(self):
        return self._test_functional_merge(
            index_query_order=['field', 'keyword', 'text'])

class Test_query_catalog(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

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

    def test_it_with_permitted_no_auth_policy(self):
        request = testing.DummyRequest()
        request.context = testing.DummyResource()
        inst = self._makeOne(request)
        inst.Search = DummySearch(True)
        inst('q', a=1, permitted='view')
        self.assertFalse(inst.Search.checker)

    def test_with_permitted_with_auth_policy(self):
        self.config.testing_securitypolicy(permissive=True)
        request = testing.DummyRequest()
        request.context = testing.DummyResource()
        inst = self._makeOne(request)
        inst.Search = DummySearch(True)
        inst('q', a=1, permitted='view')
        self.assertTrue(inst.Search.checker(request.context))

    def test_with_permitted_with_auth_policy_nonpermissive(self):
        self.config.testing_securitypolicy(permissive=False)
        request = testing.DummyRequest()
        request.context = testing.DummyResource()
        inst = self._makeOne(request)
        inst.Search = DummySearch(True)
        inst('q', a=1, permitted='view')
        self.assertFalse(inst.Search.checker(request.context))
        
    def test_it_with_permitted_permitted_has_iter(self):
        self.config.testing_securitypolicy(permissive=True)
        request = testing.DummyRequest()
        request.context = testing.DummyResource()
        inst = self._makeOne(request)
        inst.Search = DummySearch(True)
        inst('q', a=1, permitted=(['bob'], 'view'))
        self.assertTrue(inst.Search.checker(request.context))
        
class Test_search_catalog(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
        
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

    def test_it_with_permitted_no_auth_policy(self):
        request = testing.DummyRequest()
        request.context = testing.DummyResource()
        inst = self._makeOne(request)
        inst.Search = DummySearch(True)
        inst(a=1, permitted='view')
        self.assertFalse(inst.Search.checker)

    def test_with_permitted_with_auth_policy(self):
        self.config.testing_securitypolicy(permissive=True)
        request = testing.DummyRequest()
        request.context = testing.DummyResource()
        inst = self._makeOne(request)
        inst.Search = DummySearch(True)
        inst(a=1, permitted='view')
        self.assertTrue(inst.Search.checker(request.context))

    def test_with_permitted_with_auth_policy_nonpermissive(self):
        self.config.testing_securitypolicy(permissive=False)
        request = testing.DummyRequest()
        request.context = testing.DummyResource()
        inst = self._makeOne(request)
        inst.Search = DummySearch(True)
        inst(a=1, permitted='view')
        self.assertFalse(inst.Search.checker(request.context))
        
    def test_it_with_permitted_permitted_has_iter(self):
        self.config.testing_securitypolicy(permissive=True)
        request = testing.DummyRequest()
        request.context = testing.DummyResource()
        inst = self._makeOne(request)
        inst.Search = DummySearch(True)
        inst(a=1, permitted=(['bob'], 'view'))
        self.assertTrue(inst.Search.checker(request.context))

class Test_is_catalogable(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _callFUT(self, resource, registry=None):
        from .. import is_catalogable
        return is_catalogable(resource, registry)

    def test_no_registry_passed(self):
        resource = Dummy()
        resource.result = True
        self.config.registry.content = DummyContent()
        self.assertTrue(self._callFUT(resource))

    def test_true(self):
        resource = Dummy()
        resource.result = True
        registry = Dummy()
        registry.content = DummyContent()
        self.assertTrue(self._callFUT(resource, registry))

    def test_false(self):
        resource = Dummy()
        resource.result = False
        registry = Dummy()
        registry.content = DummyContent()
        self.assertFalse(self._callFUT(resource, registry))

class Test_catalog_view_factory_for(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _callFUT(self, resource, registry=None):
        from .. import catalog_view_factory_for
        return catalog_view_factory_for(resource, registry)

    def test_no_registry_passed(self):
        resource = Dummy()
        resource.result = True
        self.config.registry.content = DummyContent()
        self.assertTrue(self._callFUT(resource))

    def test_true(self):
        resource = Dummy()
        resource.result = True
        registry = Dummy()
        registry.content = DummyContent()
        self.assertEqual(self._callFUT(resource, registry), True)

    def test_supplied(self):
        resource = Dummy()
        dummyviewfactory = object()
        resource.result = dummyviewfactory
        registry = Dummy()
        registry.content = DummyContent()
        self.assertEqual(self._callFUT(resource, registry), dummyviewfactory)

class TestCatalogViewWrapper(unittest.TestCase):
    def _makeOne(self, content, view_factory):
        from .. import CatalogViewWrapper
        return CatalogViewWrapper(content, view_factory)

    def test_it(self):
        content = testing.DummyResource()
        view_factory = None
        inst = self._makeOne(content, view_factory)
        self.assertEqual(inst.content, content)
        self.assertEqual(inst.view_factory, view_factory)

class TestCatalogablePredicate(unittest.TestCase):
    def _makeOne(self, val, config):
        from .. import CatalogablePredicate
        return CatalogablePredicate(val, config)

    def test_text(self):
        config = Dummy()
        config.registry = Dummy()
        inst = self._makeOne(True, config)
        self.assertEqual(inst.text(), 'catalogable = True')

    def test_phash(self):
        config = Dummy()
        config.registry = Dummy()
        inst = self._makeOne(True, config)
        self.assertEqual(inst.phash(), 'catalogable = True')

    def test__call__(self):
        config = Dummy()
        config.registry = Dummy()
        inst = self._makeOne(True, config)
        def is_catalogable(context, registry):
            self.assertEqual(context, None)
            self.assertEqual(registry, config.registry)
            return True
        inst.is_catalogable = is_catalogable
        self.assertEqual(inst(None, None), True)


class DummySearch(object):
    def __init__(self, result):
        self.result = result

    def __call__(self, context, checker=None):
        self.checker = checker
        return self

    def query(self, *arg, **kw):
        return self.result

    def search(self, **kw):
        return self.result

class DummyQuery(object):
    pass    

class DummyObjectMap(object):
    def __init__(self, objectid_to=None): 
        if objectid_to is None: objectid_to = {}
        self.objectid_to = objectid_to

    def path_for(self, objectid):
        data = self.objectid_to.get(objectid)
        if data is None: return
        return data[1]

    def object_for(self, objectid):
        data = self.objectid_to.get(objectid)
        if data is None:
            return
        return data[0]

class DummyCatalogQuery(object):
    family = BTrees.family64
    def __init__(self, result=(0, [])):
        self.result = result

    def query(self, q, **kw):
        return self.result

    def search(self, **kw):
        return self.result

    def sort(self, *arg, **kw):
        return self.result

    def __call__(self, catalog, family=None):
        self.catalog = catalog
        if family is not None:
            self.family = family
        return self

class DummyCatalog(dict):
    pass

class DummyTransaction(object):
    def __init__(self):
        self.committed = 0
        self.aborted = 0
        
    def commit(self):
        self.committed += 1

    def abort(self):
        self.aborted += 1
        

@implementer(IIndex)
class DummyIndex(object):

    value = None
    docid = None
    limit = None
    sort_type = None

    def __init__(self, *arg, **kw):
        self.arg = arg
        self.kw = kw

    def index_doc(self, docid, value):
        self.docid = docid
        self.value = value
        return value

    def unindex_doc(self, docid):
        self.unindexed = docid

    def reset(self):
        self.cleared = True

    def reindex_doc(self, docid, object):
        self.reindexed_docid = docid
        self.reindexed_ob = object

    def apply(self, query):
        return self.arg[0]

    def apply_intersect(self, query, docids): # pragma: no cover
        if docids is None:
            return self.arg[0]
        L = []
        for docid in self.arg[0]:
            if docid in docids:
                L.append(docid)
        return L

    def sort(self, results, reverse=False, limit=None, sort_type=None):
        self.limit = limit
        self.sort_type = sort_type
        if reverse:
            return ['sorted3', 'sorted2', 'sorted1']
        return ['sorted1', 'sorted2', 'sorted3']

class DummyContent(object):
    def metadata(self, resource, name, default=None):
        return getattr(resource, 'result', default)
        

class Dummy(object):
    pass

class DummyContentRegistry(object):
    def metadata(self, resource, name, default=None):
        return True

