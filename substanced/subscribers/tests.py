import unittest

from pyramid import testing

from pyramid.traversal import resource_path_tuple

class Test__postorder(unittest.TestCase):
    def setUp(self):
        testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _callFUT(self, node):
        from . import _postorder
        return _postorder(node)

    def test_None_node(self):
        result = list(self._callFUT(None))
        self.assertEqual(result, [None])

    def test_IFolder_node_no_children(self):
        from ..interfaces import IFolder
        model = testing.DummyResource(__provides__=IFolder)
        result = list(self._callFUT(model))
        self.assertEqual(result, [model])

    def test_IFolder_node_nonfolder_children(self):
        from ..interfaces import IFolder
        model = testing.DummyResource(__provides__=IFolder)
        one = testing.DummyResource()
        two = testing.DummyResource()
        model['one'] = one
        model['two'] = two
        result = list(self._callFUT(model))
        self.assertEqual(result, [two, one, model])

    def test_IFolder_node_folder_children(self):
        from ..interfaces import IFolder
        model = testing.DummyResource(__provides__=IFolder)
        one = testing.DummyResource()
        two = testing.DummyResource(__provides__=IFolder)
        model['one'] = one
        model['two'] = two
        three = testing.DummyResource()
        four = testing.DummyResource()
        two['three'] = three
        two['four'] = four
        result = list(self._callFUT(model))
        self.assertEqual(result, [four, three, two, one, model])

class Test_object_added(unittest.TestCase):
    def setUp(self):
        testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _callFUT(self, object, event):
        from . import object_added
        return object_added(object, event)

    def test_content_object_no_catalog(self):
        model = testing.DummyResource()
        self._callFUT(model, None) # doesnt blow up

    def test_content_object(self):
        from ..interfaces import ICatalogSite, ICatalogable, IObjectmapSite
        catalog = DummyCatalog()
        objectmap = DummyObjectMap()
        model = testing.DummyResource(
            objectmap=objectmap, catalog=catalog,
            __provides__=(ICatalogSite, ICatalogable, IObjectmapSite)
            )
        self._callFUT(model, None)
        self.assertEqual(objectmap.added, [model])
        self.assertEqual(catalog.indexed, [(1, model)])

class Test_object_removed(unittest.TestCase):
    def setUp(self):
        testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _callFUT(self, object, event):
        from . import object_removed
        return object_removed(object, event)

    def test_content_object_no_objectmap(self):
        model = testing.DummyResource()
        self._callFUT(model, None) # doesnt blow up

    def test_content_object_w_objectmap_and_catalog(self):
        from ..interfaces import ICatalogSite, IObjectmapSite
        objectmap = DummyObjectMap({1: (u'',)})
        catalog = DummyCatalog()
        catalog.objectids = [1]
        model = testing.DummyResource(
            objectmap=objectmap, catalog=catalog,
            __provides__=(ICatalogSite, IObjectmapSite),
            )
        self._callFUT(model, None)
        self.assertEqual(catalog.unindexed, [1])
        self.assertEqual(objectmap.removed, [1])

class Test_object_modified(unittest.TestCase):
    def setUp(self):
        testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _callFUT(self, object, event):
        from . import object_modified
        return object_modified(object, event)

    def test_content_object_no_catalog(self):
        model = testing.DummyResource()
        self._callFUT(model, None) # doesnt blow up

    def test_content_object(self):
        from ..interfaces import ICatalogSite, ICatalogable, IObjectmapSite
        objectmap = DummyObjectMap({1:(u'',)})
        catalog = DummyCatalog()
        model = testing.DummyResource(
            objectmap=objectmap, catalog=catalog,
            __provides__=(ICatalogSite, ICatalogable, IObjectmapSite),
            )
        self._callFUT(model, None)
        self.assertEqual(catalog.reindexed, [(1, model)])

    def test_content_object_not_yet_indexed(self):
        from ..interfaces import ICatalogSite, ICatalogable, IObjectmapSite
        catalog = DummyCatalog()
        objectmap = DummyObjectMap()
        model = testing.DummyResource(
            catalog = catalog, objectmap=objectmap,
            __provides__=(ICatalogSite, ICatalogable, IObjectmapSite)
            )
        self._callFUT(model, None)
        self.assertEqual(catalog.reindexed, [])
        self.assertEqual(model.__objectid__, 1)
        self.assertEqual(catalog.indexed, [(1, model)])
        
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
    def __init__(self, objectid_to_path=None):
        if objectid_to_path is None:
            objectid_to_path = {}
        self.objectid_to_path = dict(objectid_to_path)
        self.path_to_objectid = {}
        for k, v in objectid_to_path.items():
            self.path_to_objectid[v] = k
        self.added = []
        self.removed = []

    def add(self, obj):
        self.added.append(obj)
        objectid = getattr(obj, '__objectid__', None)
        if objectid is None:
            objectid = 1
            obj.__objectid__ = objectid
        return objectid

    def objectid_for(self, obj):
        path_tuple = resource_path_tuple(obj)
        return self.path_to_objectid.get(path_tuple)

    def remove(self, v):
        path_tuple = resource_path_tuple(v)
        objectid = self.path_to_objectid[path_tuple]
        self.removed.append(objectid)
        return [objectid]

