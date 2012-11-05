import unittest
from pyramid import testing

import BTrees

def _makeSite(**kw):
    from ...interfaces import IFolder
    from zope.interface import alsoProvides
    site = testing.DummyResource(__provides__=kw.pop('__provides__', None))
    alsoProvides(site, IFolder)
    for k, v in kw.items():
        site[k] = v
    site.__services__ = tuple(kw.keys())
    return site

class TestResolvingIndex(unittest.TestCase):
    def _makeOne(self):
        from ..indexes import ResolvingIndex
        return ResolvingIndex()

    def test_resultset_from_query_no_resolver(self):
        inst = self._makeOne()
        inst.__objectmap__ = DummyObjectmap()
        query = DummyQuery()
        resultset = inst.resultset_from_query(query)
        self.assertEqual(resultset.ids, [1,2,3])
        self.assertEqual(resultset.resolver, inst.__objectmap__.object_for)

    def test_resultset_from_query_with_resolver(self):
        inst = self._makeOne()
        inst.__objectmap__ = DummyObjectmap()
        query = DummyQuery()
        resolver = object()
        resultset = inst.resultset_from_query(query, resolver=resolver)
        self.assertEqual(resultset.ids, [1,2,3])
        self.assertEqual(resultset.resolver, resolver)

class TestPathIndex(unittest.TestCase):
    def _makeOne(self, family=None):
        from ..indexes import PathIndex
        from ...objectmap import ObjectMap
        catalog = DummyCatalog()
        index = PathIndex(family=family)
        index.__parent__ = catalog
        site = _makeSite(catalog=catalog)
        objectmap = ObjectMap(site)
        site.__objectmap__ = objectmap
        return index

    def _acquire(self, inst, name):
        from substanced.util import acquire
        return acquire(inst, name)

    def test_document_repr(self):
        from substanced.util import oid_of
        inst = self._makeOne()
        obj = testing.DummyResource()
        objectmap = self._acquire(inst, '__objectmap__')
        objectmap.add(obj, (u'',))
        result = inst.document_repr(oid_of(obj))
        self.assertEqual(result, (u'',))

    def test_document_repr_missing(self):
        inst = self._makeOne()
        result = inst.document_repr(1)
        self.assertEqual(result, None)

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
        objectmap = self._acquire(inst, '__objectmap__')
        objectmap._v_nextid = 1
        objectmap.add(obj, (u'',))
        result = inst.search((u'',))
        self.assertEqual(list(result),  [1])

    def test_apply_obj(self):
        inst = self._makeOne()
        obj = testing.DummyResource()
        objectmap = self._acquire(inst, '__objectmap__')
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
        objectmap = self._acquire(inst, '__objectmap__')
        objectmap._v_nextid = 1
        objectmap.add(obj, (u'',))
        result = inst.apply((u'',))
        self.assertEqual(list(result),  [1])

    def test_apply_dict(self):
        inst = self._makeOne()
        obj = testing.DummyResource()
        objectmap = self._acquire(inst, '__objectmap__')
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
        objectmap = self._acquire(inst, '__objectmap__')
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
        objectmap = self._acquire(inst, '__objectmap__')
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
        objectmap = self._acquire(inst, '__objectmap__')
        objectmap._v_nextid = 1
        objectmap.add(obj, (u'',))
        result = inst.apply_intersect(obj, objectmap.family.IF.Set([1]))
        self.assertEqual(list(result),  [1])

    def test_eq_defaults(self):
        inst = self._makeOne()
        result = inst.eq('/abc')
        self.assertEqual(
            result._value,
            {'path': '/abc'}
            )

    def test_eq_include_origin_is_False(self):
        inst = self._makeOne()
        inst.depth = 10
        result = inst.eq('/abc', include_origin=False)
        self.assertEqual(
            result._value,
            {'path': '/abc', 'include_origin': False}
            )

    def test_eq_include_depth_is_not_None(self):
        inst = self._makeOne()
        inst.depth = 10
        result = inst.eq('/abc', depth=1)
        self.assertEqual(
            result._value,
            {'path': '/abc', 'depth': 1}
            )

class TestAllowedIndex(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
        
    def _makeOne(self, discriminator=None, family=None):
        if discriminator is None:
            discriminator = 'allowed'
        from ..indexes import AllowedIndex
        index = AllowedIndex(discriminator, family=family)
        return index

    def test_allows_request_default_permission(self):
        index = self._makeOne()
        request = testing.DummyRequest()
        q = index.allows(request)
        self.assertEqual(q._value, [('system.Everyone', 'view')])

    def test_allows_request_nondefault_permission(self):
        index = self._makeOne()
        request = testing.DummyRequest()
        q = index.allows(request, 'edit')
        self.assertEqual(q._value, [('system.Everyone', 'edit')])

    def test_allows_iterable(self):
        index = self._makeOne()
        q = index.allows(['bob', 'joe'], 'edit')
        self.assertEqual(q._value, [('bob', 'edit'), ('joe', 'edit')])

    def test_allows_single(self):
        index = self._makeOne()
        q = index.allows('bob', 'edit')
        self.assertEqual(q._value, [('bob', 'edit')])

class TestIndexPropertySheet(unittest.TestCase):
    def _makeOne(self, context, request):
        from ..indexes import IndexPropertySheet
        return IndexPropertySheet(context, request)

    def test_get(self):
        context = testing.DummyResource()
        context.sd_category = 'foo'
        inst = self._makeOne(context, None)
        self.assertEqual(inst.get(), {'category':'foo'})
        
    def test_set(self):
        context = testing.DummyResource()
        context.sd_category = 'foo'
        inst = self._makeOne(context, None)
        inst.set({'category':'bar'})
        self.assertEqual(context.sd_category, 'bar')
                 

class TestFacetIndexPropertySheet(unittest.TestCase):
    def setUp(self):
        testing.setUp()

    def tearDown(self):
        testing.tearDown()
        
    def _makeOne(self, context, request):
        from ..indexes import FacetIndexPropertySheet
        return FacetIndexPropertySheet(context, request)

    def test_get(self):
        context = testing.DummyResource()
        context.sd_category = 'foo'
        context.facets = ('facets',)
        inst = self._makeOne(context, None)
        self.assertEqual(inst.get(), {'category':'foo', 'facets':('facets',)})
        
    def test_set_same_facets(self):
        context = testing.DummyResource()
        context.sd_category = 'foo'
        context.facets = ('facets',)
        inst = self._makeOne(context, None)
        inst.set({'category':'bar', 'facets':['facets']})
        self.assertEqual(context.sd_category, 'bar')
                 
    def test_set_different_facets(self):
        context = testing.DummyResource()
        context.sd_category = 'foo'
        context.facets = ('facets',)
        context.__name__ = 'name'
        catalog = DummyCatalog()
        context.__parent__ = catalog
        request = testing.DummyRequest()
        inst = self._makeOne(context, request)
        inst.set({'category':'bar', 'facets':['facet1', 'facet2']})
        self.assertEqual(context.sd_category, 'bar')
        self.assertEqual(context.facets, ('facet1', 'facet2'))
        self.assertEqual(catalog.reindexed, ('name',))

class TestFacetAllowedIndexPropertySheet(unittest.TestCase):
    def setUp(self):
        testing.setUp()

    def tearDown(self):
        testing.tearDown()
        
    def _makeOne(self, context, request):
        from ..indexes import AllowedIndexPropertySheet
        return AllowedIndexPropertySheet(context, request)

    def test_get(self):
        context = testing.DummyResource()
        context.sd_category = 'foo'
        discriminator = Dummy()
        context.discriminator = discriminator
        context.discriminator.permissions = ('b', 'a')
        inst = self._makeOne(context, None)
        self.assertEqual(inst.get(),
                         {'category':'foo', 'permissions':('b', 'a')})

    def test_get_permissions_is_None(self):
        context = testing.DummyResource()
        context.sd_category = 'foo'
        discriminator = Dummy()
        context.discriminator = discriminator
        context.discriminator.permissions = None
        inst = self._makeOne(context, None)
        self.assertEqual(inst.get(),
                         {'category':'foo', 'permissions':()})

    def test_set_same_permissions(self):
        context = testing.DummyResource()
        context.sd_category = 'foo'
        discriminator = Dummy()
        context.discriminator = discriminator
        context.discriminator.permissions = ('a', 'b')
        inst = self._makeOne(context, None)
        inst.set({'category':'bar', 'permissions':('b', 'a')})
        self.assertEqual(context.sd_category, 'bar')

    def test_set_no_permissions(self):
        context = testing.DummyResource()
        context.sd_category = 'foo'
        discriminator = Dummy()
        context.discriminator = discriminator
        context.discriminator.permissions = None
        inst = self._makeOne(context, None)
        inst.set({'category':'bar', 'permissions':()})
        self.assertEqual(context.sd_category, 'bar')
        self.assertEqual(context.discriminator.permissions, None)
                 
    def test_set_different_permissions(self):
        context = testing.DummyResource()
        context.sd_category = 'foo'
        discriminator = Dummy()
        context.discriminator = discriminator
        context.discriminator.permissions = ('a','b')
        context.__name__ = 'name'
        catalog = DummyCatalog()
        context.__parent__ = catalog
        request = testing.DummyRequest()
        inst = self._makeOne(context, request)
        inst.set({'category':'bar', 'permissions':['d', 'c']})
        self.assertEqual(context.sd_category, 'bar')
        self.assertEqual(context.discriminator.permissions, ('c', 'd'))
        self.assertEqual(catalog.reindexed, ('name',))

class Dummy(object):
    pass

class DummyCatalog(object):
    family = BTrees.family64
    def __init__(self, objectids=None):
        if objectids is None:
            objectids = self.family.II.TreeSet()
        self.objectids = objectids

    def reindex(self, indexes=None, registry=None):
        self.reindexed = indexes

class DummyObjectmap(object):
    def object_for(self, docid): return 'a'

class DummyQuery(object):
    def _apply(self, names):
        return [1,2,3]
    
