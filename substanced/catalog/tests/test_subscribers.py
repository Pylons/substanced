import unittest
import BTrees

from zope.interface import alsoProvides

from pyramid import testing

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
        model1.__objectid__ = 1
        model1.__factory_type__ = 'factory1'
        model2 = testing.DummyResource()
        model2.__objectid__ = 2
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
        self.assertEqual(catalog.indexed, [(2, model2), (1, model1)])
        
    def test_catalogable_objects_disjoint(self):
        from ...interfaces import IFolder
        catalog = DummyCatalog()
        objectmap = DummyObjectMap()
        site = _makeSite(objectmap=objectmap, catalog=catalog)
        model1 = testing.DummyResource(__provides__=IFolder)
        model1.__factory_type__ = 'factory1'
        model2 = testing.DummyResource()
        model2.__objectid__ = 1
        model2.__factory_type__ = 'factory2'
        model1['model2'] = model2
        site['model1'] = model1
        event = DummyEvent(model1, None)
        content = DummyContent(
            metadata={'factory2':{'catalog':True}})
        registry = DummyRegistry(content=content)
        event.registry = registry
        self._callFUT(event)
        self.assertEqual(catalog.indexed, [(1, model2)])

    def test_multiple_catalogs(self):
        from ...interfaces import IFolder
        catalog1 = DummyCatalog()
        catalog2 = DummyCatalog()
        objectmap = DummyObjectMap()
        inner_site = _makeSite(catalog=catalog2)
        inner_site.__objectid__ = -1
        outer_site = _makeSite(objectmap=objectmap, catalog=catalog1)
        outer_site['inner'] = inner_site
        model1 = testing.DummyResource(__provides__=(IFolder,))
        model1.__objectid__ = 1
        model1.__factory_type__ = 'factory1'
        model2 = testing.DummyResource()
        model2.__objectid__ = 2
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
        self.assertEqual(catalog1.indexed, [(2, model2), (1, model1)])
        self.assertEqual(catalog2.indexed, [(2, model2), (1, model1)])

class Test_object_will_be_removed(unittest.TestCase):
    def _callFUT(self, event):
        from ..subscribers import object_will_be_removed
        return object_will_be_removed(event)

    def test_no_objectmap(self):
        model = testing.DummyResource()
        event = testing.DummyResource(object=model)
        self._callFUT(event) # doesnt blow up

    def test_no_catalog(self):
        model = testing.DummyResource()
        objectmap = DummyObjectMap()
        site = _makeSite(objectmap=objectmap)
        site['model'] = model
        model.__objectid__ = 1
        event = DummyEvent(model, None)
        self._callFUT(event) # doesnt blow up

    def test_with_pathlookup(self):
        model = testing.DummyResource()
        catalog = DummyCatalog()
        catalog.objectids = catalog.family.IF.Set([1,2])
        objectmap = DummyObjectMap()
        site = _makeSite(objectmap=objectmap, catalog=catalog)
        site['model'] = model
        model.__objectid__ = 1
        event = DummyEvent(model, None)
        self._callFUT(event)
        self.assertEqual(catalog.unindexed, [1,2])

    def test_with_pathlookup_limited_by_objectids(self):
        model = testing.DummyResource()
        catalog = DummyCatalog()
        catalog.objectids = catalog.family.IF.Set([1])
        objectmap = DummyObjectMap()
        site = _makeSite(objectmap=objectmap, catalog=catalog)
        site['model'] = model
        model.__objectid__ = 1
        event = DummyEvent(model, None)
        self._callFUT(event)
        self.assertEqual(catalog.unindexed, [1])

    def test_multiple_catalogs(self):
        model = testing.DummyResource()
        catalog1 = DummyCatalog()
        catalog1.objectids = catalog1.family.IF.Set([1])
        catalog2 = DummyCatalog()
        catalog2.objectids = catalog2.family.IF.Set([2])
        objectmap = DummyObjectMap()
        outer = _makeSite(objectmap=objectmap, catalog=catalog1)
        inner = _makeSite(catalog=catalog2)
        inner.__objectid__ = -1
        inner['model'] = model
        outer['inner'] = inner
        model.__objectid__ = 1
        event = DummyEvent(model, None)
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
        model.__objectid__ = 1
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
        model.__objectid__ = 1
        model.__factory_type__ = 'factory1'
        site['model'] = model
        event = DummyEvent(model, site)
        content = DummyContent(
            metadata={'factory1':{'catalog':True}})
        registry = DummyRegistry(content=content)
        event.registry = registry
        self._callFUT(event)
        self.assertEqual(catalog.reindexed, [(1, model)])

    def test_multiple_catalogs(self):
        objectmap = DummyObjectMap()
        catalog1 = DummyCatalog()
        catalog2 = DummyCatalog()
        outer = _makeSite(objectmap=objectmap, catalog=catalog1)
        inner = _makeSite(catalog=catalog2)
        inner.__objectid__ = -1
        outer['inner'] = inner
        model = testing.DummyResource()
        model.__objectid__ = 1
        model.__factory_type__ = 'factory1'
        inner['model'] = model
        outer['inner'] = inner
        event = DummyEvent(model, None)
        content = DummyContent(
            metadata={'factory1':{'catalog':True}})
        registry = DummyRegistry(content=content)
        event.registry = registry
        self._callFUT(event)
        self.assertEqual(catalog1.reindexed, [(1, model)])
        self.assertEqual(catalog2.reindexed, [(1, model)])

class DummyCatalog(dict):
    
    family = BTrees.family64
    
    def __init__(self):
        self.queries = []
        self.indexed = []
        self.unindexed = []
        self.reindexed = []
        self.objectids = self.family.II.TreeSet()

    def index_doc(self, objectid, obj):
        self.indexed.append((objectid, obj))

    def unindex_doc(self, objectid):
        self.unindexed.append(objectid)

    def reindex_doc(self, objectid, obj):
        self.reindexed.append((objectid, obj))

class DummyObjectMap:
    family = BTrees.family64
    
    def pathlookup(self, obj):
        return self.family.IF.Set([1,2])

class DummyEvent(object):
    def __init__(self, object, parent):
        self.object = object
        self.parent = parent
        
class DummyContent(object):
    def __init__(self, metadata):
        self._metadata = metadata

    def metadata(self, resource, name, default=None):
        return self._metadata.get(resource.__factory_type__, default)

class DummyRegistry(object):
    def __init__(self, content):
        self.content = content
        
        
