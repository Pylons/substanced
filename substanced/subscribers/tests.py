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
        from ..interfaces import ICatalogSite, ICatalogable, IDocmapSite
        catalog = DummyCatalog()
        docmap = DummyDocumentMap()
        model = testing.DummyResource(
            docmap=docmap, catalog=catalog,
            __provides__=(ICatalogSite, ICatalogable, IDocmapSite)
            )
        path = resource_path_tuple(model)
        self._callFUT(model, None)
        self.assertEqual(docmap.added, [(None, path)])
        self.assertEqual(catalog.indexed, [(1, model)])
        self.assertEqual(model.__docid__, 1)

    def test_content_object_w_existing_docid(self):
        from ..interfaces import ICatalogSite, ICatalogable, IDocmapSite
        catalog = DummyCatalog()
        docmap = DummyDocumentMap()
        model = testing.DummyResource(
            docmap=docmap, catalog=catalog, __docid__ = 123,
            __provides__=(ICatalogSite, ICatalogable, IDocmapSite),
            )
        path = resource_path_tuple(model)
        self._callFUT(model, None)
        self.assertEqual(docmap.added, [(123, path)])
        self.assertEqual(catalog.indexed, [(123, model)])

class Test_object_removed(unittest.TestCase):
    def setUp(self):
        testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _callFUT(self, object, event):
        from . import object_removed
        return object_removed(object, event)

    def test_content_object_no_docmap(self):
        model = testing.DummyResource()
        self._callFUT(model, None) # doesnt blow up

    def test_content_object_w_docmap_and_catalog(self):
        from ..interfaces import ICatalogSite, IDocmapSite
        docmap = DummyDocumentMap({1: (u'',)})
        catalog = DummyCatalog()
        catalog.docids = [1]
        model = testing.DummyResource(
            docmap=docmap, catalog=catalog,
            __provides__=(ICatalogSite, IDocmapSite),
            )
        self._callFUT(model, None)
        self.assertEqual(catalog.unindexed, [1])
        self.assertEqual(docmap.removed, [1])

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
        from ..interfaces import ICatalogSite, ICatalogable, IDocmapSite
        docmap = DummyDocumentMap({1:(u'',)})
        catalog = DummyCatalog()
        model = testing.DummyResource(
            docmap=docmap, catalog=catalog,
            __provides__=(ICatalogSite, ICatalogable, IDocmapSite),
            )
        self._callFUT(model, None)
        self.assertEqual(catalog.reindexed, [(1, model)])

    def test_content_object_not_yet_indexed(self):
        from ..interfaces import ICatalogSite, ICatalogable, IDocmapSite
        catalog = DummyCatalog()
        docmap = DummyDocumentMap()
        model = testing.DummyResource(
            catalog = catalog, docmap=docmap,
            __provides__=(ICatalogSite, ICatalogable, IDocmapSite)
            )
        self._callFUT(model, None)
        self.assertEqual(catalog.reindexed, [])
        self.assertEqual(model.__docid__, 1)
        self.assertEqual(catalog.indexed, [(1, model)])
        
class DummyCatalog(dict):
    def __init__(self):
        from BTrees.IIBTree import IITreeSet
        self.queries = []
        self.indexed = []
        self.unindexed = []
        self.reindexed = []
        self.docids = IITreeSet()

    def index_doc(self, docid, obj):
        self.indexed.append((docid, obj))

    def unindex_doc(self, docid):
        self.unindexed.append(docid)

    def reindex_doc(self, docid, obj):
        self.reindexed.append((docid, obj))

class DummyDocumentMap:
    def __init__(self, docid_to_path=None):
        if docid_to_path is None:
            docid_to_path = {}
        self.docid_to_path = dict(docid_to_path)
        self.path_to_docid = {}
        for k, v in docid_to_path.items():
            self.path_to_docid[v] = k
        self.added = []
        self.removed = []

    def add(self, path, docid=None):
        self.added.append((docid, path))
        return 1

    def remove(self, v):
        docid = self.path_to_docid[v]
        self.removed.append(docid)
        return [docid]

