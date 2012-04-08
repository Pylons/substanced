import unittest

from zope.interface import alsoProvides

from pyramid import testing

from pyramid.traversal import resource_path_tuple

def _makeSite(**kw):
    from ...interfaces import IFolder
    site = testing.DummyResource(__provides__=kw.pop('__provides__', None))
    alsoProvides(site, IFolder)
    services = testing.DummyResource()
    for k, v in kw.items():
        services[k] = v
    site['__services__'] = services
    return site

class Test_object_added(unittest.TestCase):
    def _callFUT(self, object, event):
        from ..subscribers import object_added
        return object_added(object, event)

    def test_no_catalog(self):
        model = testing.DummyResource()
        self._callFUT(model, None) # doesnt blow up

    def test_catalogable_objects(self):
        from ...interfaces import ICatalogable, IFolder
        catalog = DummyCatalog()
        objectmap = DummyObjectMap()
        site = _makeSite(objectmap=objectmap, catalog=catalog)
        model1 = testing.DummyResource(__provides__=(IFolder, ICatalogable))
        model1.__objectid__ = 1
        model2 = testing.DummyResource(__provides__=ICatalogable)
        model2.__objectid__ = 2
        model1['model2'] = model2
        site['model1'] = model1
        event = DummyEvent(None)
        self._callFUT(model1, event)
        self.assertEqual(catalog.indexed, [(2, model2), (1, model1)])
        
    def test_catalogable_objects_disjoint(self):
        from ...interfaces import ICatalogable, IFolder
        catalog = DummyCatalog()
        objectmap = DummyObjectMap()
        site = _makeSite(objectmap=objectmap, catalog=catalog)
        model1 = testing.DummyResource(__provides__=IFolder)
        model2 = testing.DummyResource(__provides__=ICatalogable)
        model2.__objectid__ = 1
        model1['model2'] = model2
        site['model1'] = model1
        event = DummyEvent(None)
        self._callFUT(model1, event)
        self.assertEqual(catalog.indexed, [(1, model2)])

class Test_object_will_be_removed(unittest.TestCase):
    def _callFUT(self, object, event):
        from ..subscribers import object_will_be_removed
        return object_will_be_removed(object, event)

    def test_no_objectmap(self):
        model = testing.DummyResource()
        self._callFUT(model, None) # doesnt blow up

    def test_no_catalog(self):
        model = testing.DummyResource()
        objectmap = DummyObjectMap()
        site = _makeSite(objectmap=objectmap)
        site['model'] = model
        model.__objectid__ = 1
        event = DummyEvent(None)
        self._callFUT(model, event) # doesnt blow up

    def test_with_pathlookup(self):
        model = testing.DummyResource()
        catalog = DummyCatalog()
        catalog.objectids = [1,2]
        objectmap = DummyObjectMap()
        site = _makeSite(objectmap=objectmap, catalog=catalog)
        site['model'] = model
        model.__objectid__ = 1
        event = DummyEvent(None)
        self._callFUT(model, event)
        self.assertEqual(catalog.unindexed, [1,2])

    def test_with_pathlookup_limited_by_objectids(self):
        model = testing.DummyResource()
        catalog = DummyCatalog()
        catalog.objectids = [1]
        objectmap = DummyObjectMap()
        site = _makeSite(objectmap=objectmap, catalog=catalog)
        site['model'] = model
        model.__objectid__ = 1
        event = DummyEvent(None)
        self._callFUT(model, event)
        self.assertEqual(catalog.unindexed, [1])
        
class Test_object_modified(unittest.TestCase):
    def _callFUT(self, object, event):
        from ..subscribers import object_modified
        return object_modified(object, event)

    def test_no_catalog(self):
        from ...interfaces import ICatalogable
        objectmap = DummyObjectMap()
        site = _makeSite(objectmap=objectmap)
        model = testing.DummyResource(__provides__=ICatalogable)
        model.__objectid__ = 1
        site['model'] = model
        event = DummyEvent(site)
        self._callFUT(model, event) # doesnt blow up
        
    def test_catalogable_object(self):
        from ...interfaces import ICatalogable
        objectmap = DummyObjectMap()
        catalog = DummyCatalog()
        site = _makeSite(objectmap=objectmap, catalog=catalog)
        model = testing.DummyResource(__provides__=ICatalogable)
        model.__objectid__ = 1
        site['model'] = model
        event = DummyEvent(site)
        self._callFUT(model, event)
        self.assertEqual(catalog.reindexed, [(1, model)])

    def test_uncatalogable_object(self):
        objectmap = DummyObjectMap()
        catalog = DummyCatalog()
        site = _makeSite(objectmap=objectmap, catalog=catalog)
        model = testing.DummyResource()
        model.__objectid__ = 1
        site['model'] = model
        event = DummyEvent(site)
        self._callFUT(model, event)
        self.assertEqual(catalog.reindexed, [])
        
class DummyCatalog(dict):
    def __init__(self):
        from BTrees.IIBTree import IITreeSet
        self.queries = []
        self.indexed = []
        self.unindexed = []
        self.reindexed = []
        self.objectids = IITreeSet()

    def index_doc(self, objectid, obj):
        self.indexed.append((objectid, obj))

    def unindex_doc(self, objectid):
        self.unindexed.append(objectid)

    def reindex_doc(self, objectid, obj):
        self.reindexed.append((objectid, obj))

class DummyObjectMap:
    def pathlookup(self, obj):
        return [1,2]

class DummyEvent(object):
    def __init__(self, parent):
        self.parent = parent
        
