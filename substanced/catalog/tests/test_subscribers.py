import unittest
import BTrees

from zope.interface import alsoProvides

from pyramid import testing

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

class Test_object_added(unittest.TestCase):
    def _callFUT(self, event):
        from ..subscribers import object_added
        return object_added(event)

    def test_no_catalog(self):
        model = testing.DummyResource()
        event = testing.DummyResource(object=model)
        self._callFUT(event) # doesnt blow up

    def test_catalogable_objects(self):
        from ...interfaces import IFolder
        catalog = DummyCatalog()
        objectmap = DummyObjectMap()
        site = _makeSite(objectmap=objectmap, catalog=catalog)
        model1 = testing.DummyResource(__provides__=(IFolder,))
        model1.__oid__ = 1
        model1.__factory_type__ = 'factory1'
        model2 = testing.DummyResource()
        model2.__oid__ = 2
        model2.__factory_type__ = 'factory2'
        model1['model2'] = model2
        site['model1'] = model1
        event = DummyEvent(model1, None)
        content = DummyContent(
            metadata={'factory1':{'catalog':True},
                      'factory2':{'catalog':True},
                      })
        registry = DummyRegistry(content=content)
        event.registry = registry
        self._callFUT(event)
        indexed = catalog.indexed
        self.assertEqual(len(indexed), 2)
        self.assertEqual(indexed[0][0], 2)
        self.assertEqual(indexed[0][1].content, model2)
        self.assertEqual(indexed[1][0], 1)
        self.assertEqual(indexed[1][1].content, model1)
        
    def test_catalogable_objects_disjoint(self):
        from ...interfaces import IFolder
        catalog = DummyCatalog()
        objectmap = DummyObjectMap()
        site = _makeSite(objectmap=objectmap, catalog=catalog)
        model1 = testing.DummyResource(__provides__=IFolder)
        model1.__factory_type__ = 'factory1'
        model2 = testing.DummyResource()
        model2.__oid__ = 1
        model2.__factory_type__ = 'factory2'
        model1['model2'] = model2
        site['model1'] = model1
        event = DummyEvent(model1, None)
        content = DummyContent(
            metadata={'factory2':{'catalog':True}})
        registry = DummyRegistry(content=content)
        event.registry = registry
        self._callFUT(event)
        indexed = catalog.indexed
        self.assertEqual(len(indexed), 1)
        self.assertEqual(indexed[0][0], 1)
        self.assertEqual(indexed[0][1].content, model2)

    def test_multiple_catalogs(self):
        from ...interfaces import IFolder
        catalog1 = DummyCatalog()
        catalog2 = DummyCatalog()
        objectmap = DummyObjectMap()
        inner_site = _makeSite(catalog=catalog2)
        inner_site.__oid__ = -1
        outer_site = _makeSite(objectmap=objectmap, catalog=catalog1)
        outer_site['inner'] = inner_site
        model1 = testing.DummyResource(__provides__=(IFolder,))
        model1.__oid__ = 1
        model1.__factory_type__ = 'factory1'
        model2 = testing.DummyResource()
        model2.__oid__ = 2
        model2.__factory_type__ = 'factory2'
        model1['model2'] = model2
        inner_site['model1'] = model1
        event = DummyEvent(model1, None)
        content = DummyContent(
            metadata={'factory1':{'catalog':True},
                      'factory2':{'catalog':True}})
        registry = DummyRegistry(content=content)
        event.registry = registry
        self._callFUT(event)
        for catalog in (catalog1, catalog2):
            indexed = catalog.indexed
            self.assertEqual(len(indexed), 2)
            self.assertEqual(indexed[0][0], 2)
            self.assertEqual(indexed[0][1].content, model2)
            self.assertEqual(indexed[1][0], 1)
            self.assertEqual(indexed[1][1].content, model1)

class Test_object_removed(unittest.TestCase):
    def _callFUT(self, event):
        from ..subscribers import object_removed
        return object_removed(event)

    def test_no_objectmap(self):
        model = testing.DummyResource()
        parent = testing.DummyResource()
        event = testing.DummyResource(object=model, parent=parent)
        self._callFUT(event) # doesnt blow up

    def test_no_catalog(self):
        site = _makeSite()
        event = DummyEvent(None, site)
        self._callFUT(event) # doesnt blow up

    def test_with_removed_oids(self):
        catalog = DummyCatalog()
        catalog.objectids = catalog.family.IF.Set([1,2])
        site = _makeSite(catalog=catalog)
        event = DummyEvent(None, site)
        event.removed_oids = catalog.family.IF.Set([1,2])
        self._callFUT(event)
        self.assertEqual(catalog.unindexed, [1,2])

    def test_with_pathlookup_limited_by_objectids(self):
        catalog = DummyCatalog()
        catalog.objectids = catalog.family.IF.Set([1])
        site = _makeSite(catalog=catalog)
        event = DummyEvent(None, site)
        event.removed_oids = catalog.family.IF.Set([1,2])
        self._callFUT(event)
        self.assertEqual(catalog.unindexed, [1])

    def test_multiple_catalogs(self):
        catalog1 = DummyCatalog()
        catalog1.objectids = catalog1.family.IF.Set([1])
        catalog2 = DummyCatalog()
        catalog2.objectids = catalog2.family.IF.Set([2])
        outer = _makeSite(catalog=catalog1)
        inner = _makeSite(catalog=catalog2)
        inner.__oid__ = -1
        outer['inner'] = inner
        event = DummyEvent(None, inner)
        event.removed_oids = catalog1.family.IF.Set([1,2])
        self._callFUT(event)
        self.assertEqual(catalog1.unindexed, [1])
        self.assertEqual(catalog2.unindexed, [2])
        
class Test_object_modified(unittest.TestCase):
    def _callFUT(self, event):
        from ..subscribers import object_modified
        return object_modified(event)

    def test_no_catalog(self):
        objectmap = DummyObjectMap()
        site = _makeSite(objectmap=objectmap)
        model = testing.DummyResource()
        model.__oid__ = 1
        model.__factory_type__ = 'factory1'
        site['model'] = model
        event = DummyEvent(model, site)
        content = DummyContent(
            metadata={'factory1':{'catalog':True}})
        registry = DummyRegistry(content=content)
        event.registry = registry
        self._callFUT(event) # doesnt blow up
        
    def test_catalogable_object(self):
        objectmap = DummyObjectMap()
        catalog = DummyCatalog()
        site = _makeSite(objectmap=objectmap, catalog=catalog)
        model = testing.DummyResource()
        model.__oid__ = 1
        model.__factory_type__ = 'factory1'
        site['model'] = model
        event = DummyEvent(model, site)
        content = DummyContent(
            metadata={'factory1':{'catalog':True}})
        registry = DummyRegistry(content=content)
        event.registry = registry
        self._callFUT(event)
        reindexed = catalog.reindexed
        self.assertEqual(len(reindexed), 1)
        self.assertEqual(reindexed[0][0], 1)
        self.assertEqual(reindexed[0][1].content, model)

    def test_multiple_catalogs(self):
        objectmap = DummyObjectMap()
        catalog1 = DummyCatalog()
        catalog2 = DummyCatalog()
        outer = _makeSite(objectmap=objectmap, catalog=catalog1)
        inner = _makeSite(catalog=catalog2)
        inner.__oid__ = -1
        outer['inner'] = inner
        model = testing.DummyResource()
        model.__oid__ = 1
        model.__factory_type__ = 'factory1'
        inner['model'] = model
        outer['inner'] = inner
        event = DummyEvent(model, None)
        content = DummyContent(
            metadata={'factory1':{'catalog':True}})
        registry = DummyRegistry(content=content)
        event.registry = registry
        self._callFUT(event)
        for catalog in (catalog1, catalog2):
            reindexed = catalog.reindexed
            self.assertEqual(len(reindexed), 1)
            self.assertEqual(reindexed[0][0], 1)
            self.assertEqual(reindexed[0][1].content, model)

class Test_acl_modified(unittest.TestCase):
    def _callFUT(self, event):
        from ..subscribers import acl_modified
        return acl_modified(event)

    def test_no_catalogs(self):
        resource = testing.DummyResource()
        event = DummyEvent(resource, None)
        self._callFUT(event) # doesnt blow up

    def test_gardenpath(self):
        resource = testing.DummyResource()
        resource.__factory_type__ = 'resource'
        resource.__oid__ = 1
        resource.__services__ = ('catalog',)
        catalog = DummyCatalog()
        resource['catalog'] = catalog
        index = DummyIndex()
        catalog['index'] = index
        event = DummyEvent(resource, None)
        content = DummyContent({'resource':True})
        event.registry = DummyRegistry(content)
        self._callFUT(event) # doesnt blow up
        self.assertEqual(index.oid, 1)
        self.assertEqual(index.data.__class__.__name__, 'CatalogViewWrapper')

class DummyCatalog(dict):
    
    family = BTrees.family64
    
    def __init__(self, result=None):
        self.queries = []
        self.indexed = []
        self.unindexed = []
        self.reindexed = []
        self.objectids = self.family.II.TreeSet()
        self.result = result

    def index_doc(self, objectid, obj):
        self.indexed.append((objectid, obj))

    def unindex_doc(self, objectid):
        self.unindexed.append(objectid)

    def reindex_doc(self, objectid, obj):
        self.reindexed.append((objectid, obj))

class DummyObjectMap:
    family = BTrees.family64
    
class DummyEvent(object):
    def __init__(self, object, parent, registry=None):
        self.object = object
        self.parent = parent
        self.registry = registry
        
class DummyContent(object):
    def __init__(self, metadata):
        self._metadata = metadata

    def metadata(self, resource, name, default=None):
        return self._metadata.get(resource.__factory_type__, default)

    def istype(self, obj, whatever):
        return True

class DummyRegistry(object):
    def __init__(self, content):
        self.content = content
        
class DummyIndex(object):
    def __init__(self):
        self.reindexed = []

    def reindex_doc(self, oid, data):
        self.oid = oid
        self.data = data
