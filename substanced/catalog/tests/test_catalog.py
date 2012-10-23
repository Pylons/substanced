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
    objectmap = kw.pop('objectmap', None)
    if objectmap is not None:
        site.__objectmap__ = objectmap
    for k, v in kw.items():
        site[k] = v
    site.__services__ = tuple(kw.keys())
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

    def test___sdi_addable__True(self):
        inst = self._makeOne()
        intr = {'meta':{'is_index':True}}
        self.assertTrue(inst.__sdi_addable__(None, intr))

    def test___sdi_addable__False(self):
        inst = self._makeOne()
        intr = {'meta':{}}
        self.assertFalse(inst.__sdi_addable__(None, intr))

    def test___sdi_butttons__(self):
        inst = self._makeOne()
        context = testing.DummyResource()
        request = testing.DummyRequest()
        buttons = inst.__sdi_buttons__(context, request)
        self.assertEqual(buttons[0],
                         {'buttons':
                          [{'text': 'Reindex',
                            'class': 'btn-primary',
                            'id': 'reindex',
                            'value': 'reindex',
                            'name': 'form.reindex'}],
                          'type': 'single'})

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

class Test_add_catalog_index_factory(unittest.TestCase):
    def _callFUT(self, config, name, factory):
        from .. import add_catalog_index_factory
        return add_catalog_index_factory(config, name, factory)

    def test_it(self):
        from pyramid.interfaces import PHASE1_CONFIG
        from .. import get_index_factories
        config = DummyConfigurator()
        self._callFUT(config, 'name', 'factory')
        self.assertEqual(len(config.actions), 1)
        action = config.actions[0]
        self.assertEqual(
            action['discriminator'],
            ('sd-catalog-index-factory', 'name')
            )
        self.assertEqual(
            action['order'], PHASE1_CONFIG
            )
        self.assertEqual(
            action['introspectables'], (config.intr,)
            )
        self.assertEqual(config.intr['name'], 'name')
        self.assertEqual(config.intr['factory'], 'factory')
        callable = action['callable']
        callable()
        self.assertEqual(
            get_index_factories(config.registry), {'name':'factory'}
            )

class Test_add_catalog_index(unittest.TestCase):
    def _callFUT(self, config, name, factory_name, category, **factory_args):
        from .. import add_catalog_index
        return add_catalog_index(
            config, name, factory_name, category, **factory_args
            )

    def test_it(self):
        from .. import get_index_factories, get_candidate_indexes
        config = DummyConfigurator()
        self._callFUT(config, 'name', 'factory_name', 'category', a=1)
        self.assertEqual(len(config.actions), 1)
        action = config.actions[0]
        self.assertEqual(
            action['discriminator'],
            ('sd-catalog-index', 'name', 'category')
            )
        self.assertEqual(
            action['introspectables'], (config.intr,)
            )
        self.assertEqual(config.intr['name'], 'name')
        self.assertEqual(config.intr['factory_name'], 'factory_name')
        self.assertEqual(config.intr['factory_args'], {'a':1})
        self.assertEqual(config.intr['category'], 'category')
        self.assertEqual(
            config.intr.relations,
            [{'name': 'sd catalog index factories', 
              'discrim': ('sd-catalog-index-factory', 'factory_name')}]
              )
        factories = get_index_factories(config.registry)
        factories['factory_name'] = 'yo'
        callable = action['callable']
        callable()
        self.assertEqual(
            get_candidate_indexes(config.registry), 
            {'category':{
                'name':{'factory_name':'factory_name', 'factory_args':{'a':1}}
                }
            }
            )

    def test_no_factory(self):
        from pyramid.exceptions import ConfigurationError
        config = DummyConfigurator()
        self._callFUT(config, 'name', 'factory_name', 'category', a=1)
        action = config.actions[0]
        callable = action['callable']
        self.assertRaises(ConfigurationError, callable)

class Test_text_index_factory(unittest.TestCase):
    def _callFUT(self, name, category, **kw):
        from .. import text_index_factory
        return text_index_factory(name, category, **kw)

    def test_it(self):
        result = self._callFUT('name', 'category')
        self.assertEqual(result.__class__.__name__, 'TextIndex')
        self.assertEqual(result.sd_category, 'category')
        self.assertEqual(result.discriminator.method_name, 'name')

    def test_it_with_discrim(self):
        result = self._callFUT('name', 'category', discriminator='abc')
        self.assertEqual(result.__class__.__name__, 'TextIndex')
        self.assertEqual(result.sd_category, 'category')
        self.assertEqual(result.discriminator, 'abc')

class Test_field_index_factory(unittest.TestCase):
    def _callFUT(self, name, category, **kw):
        from .. import field_index_factory
        return field_index_factory(name, category, **kw)

    def test_it(self):
        result = self._callFUT('name', 'category')
        self.assertEqual(result.__class__.__name__, 'FieldIndex')
        self.assertEqual(result.sd_category, 'category')
        self.assertEqual(result.discriminator.method_name, 'name')

    def test_it_with_discrim(self):
        result = self._callFUT('name', 'category', discriminator='abc')
        self.assertEqual(result.__class__.__name__, 'FieldIndex')
        self.assertEqual(result.sd_category, 'category')
        self.assertEqual(result.discriminator, 'abc')

class Test_keyword_index_factory(unittest.TestCase):
    def _callFUT(self, name, category, **kw):
        from .. import keyword_index_factory
        return keyword_index_factory(name, category, **kw)

    def test_it(self):
        result = self._callFUT('name', 'category')
        self.assertEqual(result.__class__.__name__, 'KeywordIndex')
        self.assertEqual(result.sd_category, 'category')
        self.assertEqual(result.discriminator.method_name, 'name')

    def test_it_with_discrim(self):
        result = self._callFUT('name', 'category', discriminator='abc')
        self.assertEqual(result.__class__.__name__, 'KeywordIndex')
        self.assertEqual(result.sd_category, 'category')
        self.assertEqual(result.discriminator, 'abc')

class Test_facet_index_factory(unittest.TestCase):
    def _callFUT(self, name, category, **kw):
        from .. import facet_index_factory
        return facet_index_factory(name, category, **kw)

    def test_it(self):
        result = self._callFUT('name', 'category', facets=['abc'])
        self.assertEqual(result.__class__.__name__, 'FacetIndex')
        self.assertEqual(result.sd_category, 'category')
        self.assertEqual(result.discriminator.method_name, 'name')

    def test_it_with_discrim(self):
        result = self._callFUT('name', 'category', discriminator='abc',
            facets=['abc'])
        self.assertEqual(result.__class__.__name__, 'FacetIndex')
        self.assertEqual(result.sd_category, 'category')
        self.assertEqual(result.discriminator, 'abc')

class Test_allowed_index_factory(unittest.TestCase):
    def _callFUT(self, name, category, **kw):
        from .. import allowed_index_factory
        return allowed_index_factory(name, category, **kw)

    def test_it(self):
        result = self._callFUT('name', 'category')
        self.assertEqual(result.__class__.__name__, 'AllowedIndex')
        self.assertEqual(result.sd_category, 'category')
        self.assertEqual(result.discriminator.method_name, 'name')

    def test_it_with_discrim(self):
        result = self._callFUT('name', 'category', discriminator='abc')
        self.assertEqual(result.__class__.__name__, 'AllowedIndex')
        self.assertEqual(result.sd_category, 'category')
        self.assertEqual(result.discriminator, 'abc')

class Test_path_index_factory(unittest.TestCase):
    def _callFUT(self, name, category, **kw):
        from .. import path_index_factory
        return path_index_factory(name, category, **kw)

    def test_it(self):
        result = self._callFUT('name', 'category')
        self.assertEqual(result.__class__.__name__, 'PathIndex')
        self.assertEqual(result.sd_category, 'category')

class Test_add_system_indexes(unittest.TestCase):
    def _callFUT(self, config):
        from .. import add_system_indexes
        return add_system_indexes(config)

    def test_it(self):
        config = DummyConfigurator()
        self._callFUT(config)
        self.assertEqual(
            config.indexes,
            ['path', 'name', 'oid', 'interfaces', 'containment', 'allowed']
            )

class DummyIntrospectable(dict):
    def __init__(self, *arg, **kw):
        dict.__init__(self, *arg, **kw)
        self.relations = []
    def relate(self, name, discrim):
        self.relations.append({'name':name, 'discrim':discrim})

class DummyConfigurator(object):
    def __init__(self):
        self.actions = []
        self.intr = DummyIntrospectable()
        self.registry = testing.DummyResource()
        self.indexes = []

    def action(self, discriminator, callable, order=None, introspectables=()):
        self.actions.append(
            {
            'discriminator':discriminator,
            'callable':callable,
            'order':order,
            'introspectables':introspectables,
            })

    def introspectable(self, category, discriminator, name, single):
        return self.intr

    def add_catalog_index(self, name, factory_name, category, **kw):
        self.indexes.append(name)

    def add_permission(self, permission):
        self.permission = permission

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

    def apply_intersect(self, query, docids): # pragma: no cover
        if docids is None:
            return self.arg[0]
        L = []
        for docid in self.arg[0]:
            if docid in docids:
                L.append(docid)
        return L

class DummyContent(object):
    def metadata(self, resource, name, default=None):
        return getattr(resource, 'result', default)
        

class Dummy(object):
    pass

class DummyContentRegistry(object):
    def metadata(self, resource, name, default=None):
        return True

