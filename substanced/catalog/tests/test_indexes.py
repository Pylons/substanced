import unittest
from pyramid import testing

import BTrees

def _makeSite(**kw):
    from ...interfaces import IFolder
    from zope.interface import alsoProvides
    site = testing.DummyResource(__provides__=kw.pop('__provides__', None))
    alsoProvides(site, IFolder)
    services = testing.DummyResource()
    for k, v in kw.items():
        services[k] = v
    site['__services__'] = services
    return site

class TestPathIndex(unittest.TestCase):
    def _makeOne(self, family=None):
        from ..indexes import PathIndex
        from ...objectmap import ObjectMap
        objectmap = ObjectMap()
        catalog = DummyCatalog()
        index = PathIndex(family=family)
        index.__parent__ = catalog
        _makeSite(catalog=catalog, objectmap=objectmap)
        return index

    def test_ctor_alternate_family(self):
        inst = self._makeOne(family=BTrees.family32)
        self.assertEqual(inst.family, BTrees.family32)

    def test_index_doc(self):
        inst = self._makeOne()
        result = inst.index_doc(1, None)
        self.assertEqual(result, None)

    def test_unindex_doc(self):
        inst = self._makeOne()
        result = inst.unindex_doc(1)
        self.assertEqual(result, None)

    def test_reindex_doc(self):
        inst = self._makeOne()
        result = inst.reindex_doc(1, None)
        self.assertEqual(result, None)

    def test_docids(self):
        inst = self._makeOne()
        result = inst.docids()
        self.assertEqual(list(result),  [])

    def test_not_indexed(self):
        inst = self._makeOne()
        result = inst.not_indexed()
        self.assertEqual(list(result),  [])
        
    def test_search(self):
        inst = self._makeOne()
        obj = testing.DummyResource()
        objectmap = inst.__parent__.__parent__['objectmap']
        objectmap._v_nextid = 1
        objectmap.add(obj, (u'',))
        result = inst.search((u'',))
        self.assertEqual(list(result),  [1])

    def test_apply_obj(self):
        inst = self._makeOne()
        obj = testing.DummyResource()
        objectmap = inst.__parent__.__parent__['objectmap']
        objectmap._v_nextid = 1
        objectmap.add(obj, (u'',))
        result = inst.apply(obj)
        self.assertEqual(list(result),  [1])

    def test_apply_obj_noresults(self):
        inst = self._makeOne()
        obj = testing.DummyResource()
        result = inst.apply(obj)
        self.assertEqual(list(result),  [])
        
    def test_apply_path(self):
        inst = self._makeOne()
        obj = testing.DummyResource()
        objectmap = inst.__parent__.__parent__['objectmap']
        objectmap._v_nextid = 1
        objectmap.add(obj, (u'',))
        result = inst.apply((u'',))
        self.assertEqual(list(result),  [1])

    def test_apply_dict(self):
        inst = self._makeOne()
        obj = testing.DummyResource()
        objectmap = inst.__parent__.__parent__['objectmap']
        objectmap._v_nextid = 1
        objectmap.add(obj, (u'',))
        obj2 = testing.DummyResource(__name__='a')
        obj2.__parent__ = obj
        objectmap.add(obj2, (u'', u'a'))
        result = inst.apply({'path':obj})
        self.assertEqual(list(result),  [1, 2])

    def test_apply_dict_withdepth(self):
        inst = self._makeOne()
        obj = testing.DummyResource()
        objectmap = inst.__parent__.__parent__['objectmap']
        objectmap._v_nextid = 1
        objectmap.add(obj, (u'',))
        obj2 = testing.DummyResource(__name__='a')
        obj2.__parent__ = obj
        objectmap.add(obj2, (u'', u'a'))
        result = inst.apply({'path':obj, 'depth':0})
        self.assertEqual(list(result),  [1])

    def test_apply_dict_with_include_origin_false(self):
        inst = self._makeOne()
        obj = testing.DummyResource()
        objectmap = inst.__parent__.__parent__['objectmap']
        objectmap._v_nextid = 1
        objectmap.add(obj, (u'',))
        obj2 = testing.DummyResource(__name__='a')
        obj2.__parent__ = obj
        objectmap.add(obj2, (u'', u'a'))
        result = inst.apply({'path':obj, 'include_origin':False})
        self.assertEqual(list(result),  [2])
        
    def test__parse_path_obj(self):
        inst = self._makeOne()
        obj = testing.DummyResource()
        result = inst._parse_path(obj)
        self.assertEqual(result, ((u'',), None, True))
        
    def test__parse_path_path_tuple(self):
        inst = self._makeOne()
        result = inst._parse_path((u'',))
        self.assertEqual(result, ((u'',), None, True))

    def test__parse_path_path_str(self):
        inst = self._makeOne()
        result = inst._parse_path('/')
        self.assertEqual(result, ((u'',), None, True))

    def test__parse_path_path_str_with_depth(self):
        inst = self._makeOne()
        result = inst._parse_path('[depth=2]/abc')
        self.assertEqual(result, ((u'', u'abc'), 2, True))

    def test__parse_path_path_str_with_origin_false(self):
        inst = self._makeOne()
        result = inst._parse_path('[include_origin=false]/abc')
        self.assertEqual(result, ((u'', u'abc'), None, False))
        
    def test__parse_path_path_str_with_depth_and_origin(self):
        inst = self._makeOne()
        result = inst._parse_path('[depth=2,include_origin=false]/abc')
        self.assertEqual(result, ((u'', u'abc'), 2, False))

    def test__parse_path_path_str_with_depth_and_origin_no_val(self):
        inst = self._makeOne()
        result = inst._parse_path('[depth=2,include_origin]/abc')
        self.assertEqual(result, ((u'', u'abc'), 2, True))

    def test__parse_path_path_invalid(self):
        inst = self._makeOne()
        self.assertRaises(ValueError, inst._parse_path, None)

    def test__parse_path_path_invalid_string_no_begin_slash(self):
        inst = self._makeOne()
        self.assertRaises(ValueError, inst._parse_path, 'abc/def')

    def test_apply_intersect(self):
        # ftest to make sure we have the right kind of Sets
        inst = self._makeOne()
        obj = testing.DummyResource()
        objectmap = inst.__parent__.__parent__['objectmap']
        objectmap._v_nextid = 1
        objectmap.add(obj, (u'',))
        result = inst.apply_intersect(obj, objectmap.family.IF.Set([1]))
        self.assertEqual(list(result),  [1])

class DummyCatalog(object):
    family = BTrees.family64
    def __init__(self, objectids=None):
        if objectids is None:
            objectids = self.family.II.TreeSet()
        self.objectids = objectids
