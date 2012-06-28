import unittest
from pyramid import testing
from zope.interface import alsoProvides
from pyramid.traversal import resource_path_tuple

class TestObjectMap(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
        
    def _makeOne(self, family=None):
        from . import ObjectMap
        return ObjectMap(family=family)

    def test_ctor_alternate_family(self):
        import BTrees
        inst = self._makeOne(family=BTrees.family32)
        self.assertEqual(inst.family, BTrees.family32)

    def test_new_objectid_empty(self):
        inst = self._makeOne()
        times = [0]
        def randrange(frm, to):
            val = times[0]
            times[0] = times[0] + 1
            return val
        inst._randrange = randrange
        result = inst.new_objectid()
        # cant get 0 back, it's irresolveable
        self.assertEqual(result, 1)
        
    def test_new_objectid_notempty(self):
        inst = self._makeOne()
        times = [0]
        def randrange(frm, to):
            val = times[0]
            times[0] = times[0] + 1
            return val
        inst._randrange = randrange
        inst.objectid_to_path[1] = True
        result = inst.new_objectid()
        self.assertEqual(result, 2)

    def test_new_objectid_gt_maxint(self):
        inst = self._makeOne()
        oob = inst.family.maxint + 1
        times = [oob, 5]
        def randrange(frm, to):
            val = times.pop(0)
            return val
        inst._randrange = randrange
        result = inst.new_objectid()
        self.assertEqual(result, 5)

    def test_objectid_for_object(self):
        obj = testing.DummyResource()
        inst = self._makeOne()
        inst.path_to_objectid[(u'',)] = 1
        self.assertEqual(inst.objectid_for(obj), 1)

    def test_objectid_for_path_tuple(self):
        inst = self._makeOne()
        inst.path_to_objectid[(u'',)] = 1
        self.assertEqual(inst.objectid_for((u'',)), 1)

    def test_objectid_for_nonsense(self):
        inst = self._makeOne()
        self.assertRaises(ValueError, inst.objectid_for, 'a')

    def test_path_for(self):
        inst = self._makeOne()
        inst.objectid_to_path[1] = 'abc'
        self.assertEqual(inst.path_for(1), 'abc')

    def test_object_for_objectid(self):
        a = testing.DummyResource()
        inst = self._makeOne()
        inst.objectid_to_path[1] = 'abc'
        inst._find_resource = lambda *arg: a
        self.assertEqual(inst.object_for(1), a)

    def test_object_for_path_tuple(self):
        a = testing.DummyResource()
        inst = self._makeOne()
        inst.objectid_to_path[1] = 'abc'
        inst._find_resource = lambda *arg: a
        self.assertEqual(inst.object_for((u'',)), a)

    def test_object_for_unknown(self):
        inst = self._makeOne()
        self.assertRaises(ValueError, inst.object_for, None)

    def test_object_for_cantbefound(self):
        inst = self._makeOne()
        inst.objectid_to_path[1] = 'abc'
        def find_resource(*arg):
            raise KeyError('a')
        inst._find_resource = find_resource
        self.assertEqual(inst.object_for(1), None)
        
    def test_object_for_path_tuple_alternate_context(self):
        a = testing.DummyResource()
        inst = self._makeOne()
        inst.objectid_to_path[1] = 'abc'
        L= []
        def find_resource(context, path_tuple):
            L.append(context)
            return a
        inst._find_resource = find_resource
        self.assertEqual(inst.object_for((u'',), 'a'), a)
        self.assertEqual(L, ['a'])

    def test__find_resource_no_context(self):
        self.config.testing_resources({'/a':1})
        inst = self._makeOne()
        inst.__parent__ = None
        self.assertEqual(inst._find_resource(None, ('', 'a')), 1)

    def test__find_resource_with_alternate_context(self):
        self.config.testing_resources({'/a':1})
        inst = self._makeOne()
        ctx = testing.DummyResource()
        self.assertEqual(inst._find_resource(ctx, ('', 'a')), 1)
        
    def test_add_already_in_path_to_objectid(self):
        inst = self._makeOne()
        obj = testing.DummyResource()
        obj.__objectid__ = 1
        inst.path_to_objectid[(u'',)] = 1
        self.assertRaises(ValueError, inst.add, obj, (u'',))

    def test_add_is_duplicated(self):
        inst = self._makeOne()
        obj = testing.DummyResource()
        obj.__objectid__ = 1
        inst.path_to_objectid[(u'',)] = 1
        self.assertRaises(ValueError, inst.add, obj, (u'',), True)

    def test_add_already_in_objectid_to_path(self):
        inst = self._makeOne()
        obj = testing.DummyResource()
        obj.__objectid__ = 1
        inst.objectid_to_path[1] = True
        self.assertRaises(ValueError, inst.add, obj, (u'',))

    def test_add_not_a_path_tuple(self):
        inst = self._makeOne()
        self.assertRaises(ValueError, inst.add, None, None)

    def test_add_traversable_object(self):
        inst = self._makeOne()
        inst._v_nextid = 1
        obj = testing.DummyResource()
        inst.add(obj, (u'',))
        self.assertEqual(inst.objectid_to_path[1], (u'',))
        self.assertEqual(obj.__objectid__, 1)
        
    def test_add_not_valid(self):
        inst = self._makeOne()
        self.assertRaises(AttributeError, inst.add, 'a', (u'',))

    def test_remove_not_an_int_or_tuple(self):
        inst = self._makeOne()
        self.assertRaises(ValueError, inst.remove, 'a')

    def test_remove_traversable_object(self):
        inst = self._makeOne()
        inst.objectid_to_path[1] = (u'',)
        inst.path_to_objectid[(u'',)] = 1
        inst.pathindex[(u'',)] = {0:[1]}
        obj = testing.DummyResource()
        inst.remove(obj)
        self.assertEqual(dict(inst.objectid_to_path), {})
        
    def test_remove_no_omap(self):
        inst = self._makeOne()
        inst.objectid_to_path[1] = (u'',)
        result = inst.remove((u'',))
        self.assertEqual(list(result), [])

    def test_pathlookup_not_valid(self):
        inst = self._makeOne()
        self.assertRaises(ValueError, inst.pathlookup, 1)

    def test_pathlookup_traversable_object(self):
        inst = self._makeOne()
        obj = testing.DummyResource()
        gen = inst.pathlookup(obj)
        result = list(gen)
        self.assertEqual(result, [])

    def test_navgen_notexist(self):
        inst = self._makeOne()
        result = inst.navgen((u'',), 99)
        self.assertEqual(result, [])

    def test_navgen_bigdepth(self):
        inst = self._makeOne()
        root = resource('/')
        a = resource('/a')
        ab = resource('/a/b')
        abc = resource('/a/b/c')
        z = resource('/z')
        for thing in root, a, ab, abc, z:
            inst.add(thing, thing.path_tuple)
        result = inst.navgen(root, 99)
        self.assertEqual(
            result, 
            [{'path': ('', u'a'), 
              'name':u'a',
              'children': [{'path': ('', u'a', u'b'), 
                            'name':u'b',
                            'children': [{'path': ('', u'a', u'b', u'c'), 
                                          'name':u'c',
                                          'children': []}]}]}, 
             {'path': ('', u'z'), 
              'name':u'z',
              'children': []}]
            )

    def test_navgen_bigdepth_notroot(self):
        inst = self._makeOne()
        root = resource('/')
        a = resource('/a')
        ab = resource('/a/b')
        abc = resource('/a/b/c')
        z = resource('/z')
        for thing in root, a, ab, abc, z:
            inst.add(thing, thing.path_tuple)
        result = inst.navgen(a, 99)
        self.assertEqual(
            result,
            [{'path': ('', u'a', u'b'), 
              'name':u'b',
              'children': [{'path': ('', u'a', u'b', u'c'), 
                            'name':u'c',
                            'children': []}]}]
            )
        
    def test_navgen_smalldepth(self):
        inst = self._makeOne()
        root = resource('/')
        a = resource('/a')
        ab = resource('/a/b')
        abc = resource('/a/b/c')
        z = resource('/z')
        for thing in root, a, ab, abc, z:
            inst.add(thing, thing.path_tuple)
        result = inst.navgen(root, 1)
        self.assertEqual(
            result,
            [{'path': ('', u'a'), 
              'name':'a',
              'children': []},
             {'path': ('', u'z'), 
              'name':u'z',
              'children': []}]
            )

    def test_navgen_smalldepth_notroot(self):
        inst = self._makeOne()
        root = resource('/')
        a = resource('/a')
        ab = resource('/a/b')
        abc = resource('/a/b/c')
        z = resource('/z')
        for thing in root, a, ab, abc, z:
            inst.add(thing, thing.path_tuple)
        result = inst.navgen(a, 1)
        self.assertEqual(
            result,
            [{'path': ('', u'a', u'b'), 
              'name':u'b',
              'children': []}]
            )
        
    def test_navgen_nodepth(self):
        inst = self._makeOne()
        root = resource('/')
        a = resource('/a')
        ab = resource('/a/b')
        abc = resource('/a/b/c')
        z = resource('/z')
        for thing in root, a, ab, abc, z:
            inst.add(thing, thing.path_tuple)
        result = inst.navgen(root, 0)
        self.assertEqual(result, [])

    def test_navgen_nodepth_notroot(self):
        inst = self._makeOne()
        root = resource('/')
        a = resource('/a')
        ab = resource('/a/b')
        abc = resource('/a/b/c')
        z = resource('/z')
        for thing in root, a, ab, abc, z:
            inst.add(thing, thing.path_tuple)
        result = inst.navgen(a, 0)
        self.assertEqual(result, [])
        
    def test_functional(self):

        def l(path, depth=None, include_origin=True):
            path_tuple = split(path)
            return sorted(
                list(objmap.pathlookup(path_tuple, depth, include_origin))
                )

        objmap = self._makeOne()
        objmap._v_nextid = 1

        root = resource('/')
        a = resource('/a')
        ab = resource('/a/b')
        abc = resource('/a/b/c')
        z = resource('/z')

        oid1 = objmap.add(ab, ab.path_tuple)
        oid2 = objmap.add(abc, abc.path_tuple)
        oid3 = objmap.add(a, a.path_tuple)
        oid4 = objmap.add(root, root.path_tuple)
        oid5 = objmap.add(z, z.path_tuple)

        # /
        nodepth = l('/')
        assert nodepth == [oid1, oid2, oid3, oid4, oid5], nodepth
        depth0 = l('/', depth=0)
        assert depth0 == [oid4], depth0
        depth1 = l('/', depth=1)
        assert depth1 == [oid3, oid4, oid5], depth1
        depth2 = l('/', depth=2)
        assert depth2 == [oid1, oid3, oid4, oid5], depth2
        depth3 = l('/', depth=3)
        assert depth3 == [oid1, oid2, oid3, oid4, oid5], depth3
        depth4 = l('/', depth=4)
        assert depth4 == [oid1, oid2, oid3, oid4, oid5], depth4

        # /a
        nodepth = l('/a')
        assert nodepth == [oid1, oid2, oid3], nodepth
        depth0 = l('/a', depth=0)
        assert depth0 == [oid3], depth0
        depth1 = l('/a', depth=1)
        assert depth1 == [oid1, oid3], depth1
        depth2 = l('/a', depth=2)
        assert depth2 == [oid1, oid2, oid3], depth2
        depth3 = l('/a', depth=3)
        assert depth3 == [oid1, oid2, oid3], depth3

        # /a/b
        nodepth = l('/a/b')
        assert nodepth == [oid1, oid2], nodepth
        depth0 = l('/a/b', depth=0)
        assert depth0 == [oid1], depth0
        depth1 = l('/a/b', depth=1)
        assert depth1 == [oid1, oid2], depth1
        depth2 = l('/a/b', depth=2)
        assert depth2 == [oid1, oid2], depth2

        # /a/b/c
        nodepth = l('/a/b/c')
        assert nodepth == [oid2], nodepth
        depth0 = l('/a/b/c', depth=0)
        assert depth0 == [oid2], depth0
        depth1 = l('/a/b/c', depth=1)
        assert depth1 == [oid2], depth1

        # remove '/a/b'
        removed = objmap.remove(oid1)
        assert removed == set([1,2])

        # /a/b/c
        nodepth = l('/a/b/c')
        assert nodepth == [], nodepth
        depth0 = l('/a/b/c', depth=0)
        assert depth0 == [], depth0
        depth1 = l('/a/b/c', depth=1)
        assert depth1 == [], depth1

        # /a/b
        nodepth = l('/a/b')
        assert nodepth == [], nodepth
        depth0 = l('/a/b', depth=0)
        assert depth0 == [], depth0
        depth1 = l('/a/b', depth=1)
        assert depth1 == [], depth1

        # /a
        nodepth = l('/a')
        assert nodepth == [oid3], nodepth
        depth0 = l('/a', depth=0)
        assert depth0 == [oid3], depth0
        depth1 = l('/a', depth=1)
        assert depth1 == [oid3], depth1

        # /
        nodepth = l('/')
        assert nodepth == [oid3, oid4, oid5], nodepth
        depth0 = l('/', depth=0)
        assert depth0 == [oid4], depth0
        depth1 = l('/', depth=1)
        assert depth1 == [oid3, oid4, oid5], depth1

        # test include_origin false with /, no depth
        nodepth = l('/', include_origin=False)
        assert nodepth == [oid3, oid5], nodepth

        # test include_origin false with /, depth=1
        depth1 = l('/', include_origin=False, depth=0)
        assert depth1 == [], depth1
        
        pathindex = objmap.pathindex
        keys = list(pathindex.keys())

        self.assertEqual(
            keys,
            [(u'',), (u'', u'a'), (u'', u'z')]
        )

        root = pathindex[(u'',)]
        self.assertEqual(len(root), 2)
        self.assertEqual(set(root[0]), set([4]))
        self.assertEqual(set(root[1]), set([3,5]))

        a = pathindex[(u'', u'a')]
        self.assertEqual(len(a), 1)
        self.assertEqual(set(a[0]), set([3]))

        z = pathindex[(u'', u'z')]
        self.assertEqual(len(z), 1)
        self.assertEqual(set(z[0]), set([5]))
        
        self.assertEqual(
            dict(objmap.objectid_to_path),
            {3: (u'', u'a'), 4: (u'',), 5: (u'', u'z')})
        self.assertEqual(
            dict(objmap.path_to_objectid),
            {(u'', u'z'): 5, (u'', u'a'): 3, (u'',): 4})

        # remove '/'
        removed = objmap.remove((u'',))
        self.assertEqual(removed, set([3,4,5]))

        assert dict(objmap.pathindex) == {}
        assert dict(objmap.objectid_to_path) == {}
        assert dict(objmap.path_to_objectid) == {}

    def test__refids_for_source_missing(self):
        inst = self._makeOne()
        self.assertRaises(ValueError, inst._refids_for, 1, 2)
        
    def test__refids_for_target_missing(self):
        inst = self._makeOne()
        inst.objectid_to_path[1] = (u'',)
        self.assertRaises(ValueError, inst._refids_for, 1, 2)

    def test__refids_for_success_oids(self):
        inst = self._makeOne()
        inst.objectid_to_path[1] = (u'',)
        inst.objectid_to_path[2] = (u'',)
        s, t = inst._refids_for(1, 2)
        self.assertEqual(s, 1)
        self.assertEqual(t, 2)

    def test__refids_for_success_objects(self):
        inst = self._makeOne()
        one = testing.DummyResource()
        one.__objectid__ = 1
        two = testing.DummyResource()
        two.__objectid__ = 2
        inst.objectid_to_path[1] = (u'',)
        inst.objectid_to_path[2] = (u'',)
        s, t = inst._refids_for(one, two)
        self.assertEqual(s, 1)
        self.assertEqual(t, 2)
        
    def test__refid_for_missing(self):
        inst = self._makeOne()
        self.assertRaises(ValueError, inst._refid_for, 1)
        
    def test__refid_for_success_oid(self):
        inst = self._makeOne()
        inst.objectid_to_path[1] = (u'',)
        oid = inst._refid_for(1)
        self.assertEqual(oid, 1)

    def test__refid_for_success_object(self):
        inst = self._makeOne()
        obj = testing.DummyResource()
        obj.__objectid__ = 1
        inst.objectid_to_path[1] = (u'',)
        oid = inst._refid_for(obj)
        self.assertEqual(oid, 1)

    def test_connect(self):
        inst = self._makeOne()
        inst.objectid_to_path[1] = (u'',)
        inst.objectid_to_path[2] = (u'', u'a')
        inst.referencemap = DummyReferenceMap()
        inst.connect(1, 2, 'ref')
        self.assertEqual(inst.referencemap['ref'], (1, 2))

    def test_disconnect(self):
        inst = self._makeOne()
        inst.objectid_to_path[1] = (u'',)
        inst.objectid_to_path[2] = (u'', u'a')
        inst.referencemap = DummyReferenceMap()
        inst.referencemap['ref'] = True
        inst.disconnect(1, 2, 'ref')
        self.assertTrue('ref' not in inst.referencemap)

    def test_disconnect_with_objects(self):
        one = testing.DummyResource(__objectid__=1)
        two = testing.DummyResource(__objectid__=2)
        inst = self._makeOne()
        inst.objectid_to_path[1] = (u'',)
        inst.objectid_to_path[2] = (u'', u'a')
        inst.referencemap = DummyReferenceMap()
        inst.referencemap['ref'] = True
        inst.disconnect(one, two, 'ref')
        self.assertTrue('ref' not in inst.referencemap)
        
    def test_sourceids(self):
        inst = self._makeOne()
        inst.objectid_to_path[1] = (u'',)
        inst.referencemap = DummyReferenceMap(sourceids=[2])
        self.assertEqual(list(inst.sourceids(1, 'ref')), [2])
        
    def test_targetids(self):
        inst = self._makeOne()
        inst.objectid_to_path[1] = (u'',)
        inst.referencemap = DummyReferenceMap(targetids=[2])
        self.assertEqual(list(inst.targetids(1, 'ref')), [2])

    def test_sources(self):
        inst = self._makeOne()
        inst.objectid_to_path[1] = (u'',)
        inst.objectid_to_path[2] = (u'', u'a')
        inst.objectid_to_path[3] = (u'', u'b')
        inst.referencemap = DummyReferenceMap(sourceids=[2, 3])
        obj = object()
        inst._find_resource = lambda *arg: obj
        self.assertEqual(list(inst.sources(1, 'ref')), [obj, obj])
        
    def test_targets(self):
        inst = self._makeOne()
        inst.objectid_to_path[1] = (u'',)
        inst.objectid_to_path[2] = (u'', u'a')
        inst.objectid_to_path[3] = (u'', u'b')
        inst.referencemap = DummyReferenceMap(targetids=[2, 3])
        obj = object()
        inst._find_resource = lambda *arg: obj
        self.assertEqual(list(inst.targets(1, 'ref')), [obj, obj])
        
class TestReferenceSet(unittest.TestCase):
    def _makeOne(self):
        from . import ReferenceSet
        return ReferenceSet()

    def test_connect_empty(self):
        refset = self._makeOne()
        refset.connect(1, 2)
        self.assertEqual(list(refset.src2target[1]), [2])
        self.assertEqual(list(refset.target2src[2]), [1])
        
    def test_connect_nonempty_overlap(self):
        refset = self._makeOne()
        refset.src2target[1] = DummyTreeSet([2])
        refset.target2src[2] = DummyTreeSet([1])
        refset.connect(1, 2)
        self.assertEqual(list(refset.src2target[1]), [2])
        self.assertEqual(list(refset.target2src[2]), [1])

    def test_connect_nonempty_nonoverlap(self):
        refset = self._makeOne()
        refset.src2target[1] = DummyTreeSet([3])
        refset.target2src[2] = DummyTreeSet([4])
        refset.connect(1, 2)
        self.assertEqual(sorted(list(refset.src2target[1])), [2, 3])
        self.assertEqual(sorted(list(refset.target2src[2])), [1, 4])

    def test_disconnect_empty(self):
        refset = self._makeOne()
        refset.disconnect(1, 2)
        self.assertEqual(list(refset.src2target.keys()), [])
        self.assertEqual(list(refset.target2src.keys()), [])
        
    def test_disconnect_nonempty(self):
        refset = self._makeOne()
        refset.src2target[1] = DummyTreeSet([2, 3])
        refset.target2src[2] = DummyTreeSet([1, 4])
        refset.disconnect(1, 2)
        self.assertEqual(list(refset.src2target[1]), [3])
        self.assertEqual(list(refset.target2src[2]), [4])

    def test_disconnect_keyerrors(self):
        refset = self._makeOne()
        refset.src2target[1] = DummyTreeSet()
        refset.target2src[2] = DummyTreeSet()
        refset.disconnect(1, 2)
        self.assertEqual(list(refset.src2target[1]), [])
        self.assertEqual(list(refset.target2src[2]), [])

    def test_targetids(self):
        refset = self._makeOne()
        dummyset = DummyTreeSet([1])
        refset.src2target[1] = dummyset
        self.assertEqual(refset.targetids(1), dummyset)
        
    def test_sourceids(self):
        refset = self._makeOne()
        dummyset = DummyTreeSet([1])
        refset.target2src[1] = dummyset
        self.assertEqual(refset.sourceids(1), dummyset)

    def test_remove_empty(self):
        refset = self._makeOne()
        self.assertEqual(list(refset.remove([1,2])), [])

    def test_remove_notempty(self):
        # emulate the result of:
        # connect(1, 2)
        # connect(3, 4)
        # connect(2, 4)
        # connect(2, 1)
        # connect(3, 5)
        src2target = {1:DummyTreeSet([2]), 3:DummyTreeSet([4, 5]), 
                      2:DummyTreeSet([4, 1])}
        target2src = {2:DummyTreeSet([1]), 4:DummyTreeSet([3, 2]),
                      1:DummyTreeSet([2]), 5:DummyTreeSet([3])}
        refset = self._makeOne()
        refset.src2target = src2target
        refset.target2src = target2src
        oids = [1,4, 10]
        result = refset.remove(oids)
        self.assertEqual(list(result), [1,4]) # 10 unmentioned
        self.assertEqual(
            src2target,
            {3:DummyTreeSet([5])}
            )
        self.assertEqual(
            target2src,
            {5:DummyTreeSet([3])}
            )

class TestReferenceMap(unittest.TestCase):
    def _makeOne(self, map=None):
        from . import ReferenceMap
        return ReferenceMap(map)

    def test_ctor(self):
        refs = self._makeOne()
        self.assertEqual(refs.refmap.__class__.__name__, 'OOBTree')

    def test_connect(self):
        refset = DummyReferenceSet()
        map = {'reftype':refset}
        refs = self._makeOne(map)
        refs.connect('a', 'b', 'reftype')
        self.assertEqual(refset.connected, [('a', 'b')])
        
    def test_disconnect(self):
        refset = DummyReferenceSet()
        map = {'reftype':refset}
        refs = self._makeOne(map)
        refs.disconnect('a', 'b', 'reftype')
        self.assertEqual(refset.disconnected, [('a', 'b')])

    def test_targetids_no_refset(self):
        refs = self._makeOne()
        self.assertEqual(list(refs.targetids('a', 'reftype')), [])
        
    def test_targetids_with_refset(self):
        refset = DummyReferenceSet(['123'])
        map = {'reftype':refset}
        refs = self._makeOne(map)
        self.assertEqual(list(refs.targetids('a', 'reftype')), ['123'])

    def test_sourceids_no_refset(self):
        refs = self._makeOne()
        self.assertEqual(list(refs.sourceids('a', 'reftype')), [])
        
    def test_sourceids_with_refset(self):
        refset = DummyReferenceSet(['123'])
        map = {'reftype':refset}
        refs = self._makeOne(map)
        self.assertEqual(list(refs.sourceids('a', 'reftype')), ['123'])

    def test_remove(self):
        L = []
        refset1 = DummyReferenceSet()
        refset2 = DummyReferenceSet()
        refset1.remove = lambda oids: L.append(oids)
        refset2.remove = lambda oids: L.append(oids)
        map = {'reftype':refset1, 'reftype2':refset2}
        refs = self._makeOne(map)
        refs.remove([1,2])
        self.assertEqual(L, [[1,2], [1,2]])

class Test_object_will_be_added(unittest.TestCase):
    def _callFUT(self, object, event):
        from . import object_will_be_added
        return object_will_be_added(object, event)

    def test_no_objectmap(self):
        model = testing.DummyResource()
        event = DummyEvent(None)
        self._callFUT(model, event) # doesnt blow up

    def test_added_object_has_children(self):
        from ..interfaces import IFolder
        objectmap = DummyObjectMap()
        site = _makeSite(objectmap=objectmap)
        one = testing.DummyModel(__provides__=IFolder)
        two = testing.DummyModel(__provides__=IFolder)
        one['two'] = two
        event = DummyEvent(site)
        event.name = 'one'
        self._callFUT(one, event)
        self.assertEqual(
            objectmap.added,
            [(two, ('', 'one', 'two')), (one, ('', 'one'))]
            )

    def test_added_object_has_children_object_has_no_name(self):
        from ..interfaces import IFolder
        objectmap = DummyObjectMap()
        site = _makeSite(objectmap=objectmap)
        one = testing.DummyModel(__provides__=IFolder)
        two = testing.DummyModel(__provides__=IFolder)
        one['two'] = two
        event = DummyEvent(site)
        event.name = 'one'
        del one.__name__
        self._callFUT(one, event)
        self.assertEqual(
            objectmap.added,
            [(two, ('', 'one', 'two')), (one, ('', 'one'))]
            )
        
    def test_added_object_has_children_not_adding_to_root(self):
        from ..interfaces import IFolder
        objectmap = DummyObjectMap()
        site = _makeSite(objectmap=objectmap)
        one = testing.DummyModel(__provides__=IFolder)
        two = testing.DummyModel(__provides__=IFolder)
        inter = testing.DummyModel()
        site['inter'] = inter
        one['two'] = two
        event = DummyEvent(inter)
        event.name = 'one'
        self._callFUT(one, event)
        self.assertEqual(
            objectmap.added,
            [(two, ('', 'inter', 'one', 'two')), (one, ('', 'inter', 'one'))]
            )
        
    def test_object_has_a_parent(self):
        from ..interfaces import IFolder
        objectmap = DummyObjectMap()
        site = _makeSite(objectmap=objectmap)
        bogusroot = testing.DummyModel(__provides__=IFolder)
        bogusparent2 = testing.DummyModel(__provides__=IFolder)
        one = testing.DummyModel(__provides__=IFolder)
        two = testing.DummyModel(__provides__=IFolder)
        bogusroot['bogusparent2'] = bogusparent2
        bogusparent2['one'] = one
        one['two'] = two
        self.assertEqual(resource_path_tuple(one), 
                         ('', 'bogusparent2', 'one'))
        event = DummyEvent(site)
        self.assertRaises(ValueError, self._callFUT, one, event)

class Test_object_removed(unittest.TestCase):
    def _callFUT(self, object, event):
        from . import object_removed
        return object_removed(object, event)

    def test_no_objectmap(self):
        model = testing.DummyResource()
        event = DummyEvent(None)
        self._callFUT(model, event) # doesnt blow up

    def test_it(self):
        model = testing.DummyResource()
        model.__objectid__ = 1
        objectmap = DummyObjectMap()
        site = _makeSite(objectmap=objectmap)
        event = DummyEvent(site)
        self._callFUT(model, event)
        self.assertEqual(objectmap.removed, [1])
        self.assertTrue(objectmap.references_removed)

    def test_moving(self):
        model = testing.DummyResource()
        model.__objectid__ = 1
        objectmap = DummyObjectMap()
        site = _makeSite(objectmap=objectmap)
        event = DummyEvent(site, moving=True)
        self._callFUT(model, event)
        self.assertEqual(objectmap.removed, [1])
        self.assertFalse(objectmap.references_removed)
        
def resource(path):
    path_tuple = split(path)
    parent = None
    for element in path_tuple:
        obj = testing.DummyResource()
        obj.__parent__ = parent
        obj.__name__ = element
        parent = obj
    obj.path_tuple = path_tuple
    return obj
                
        
def split(s):
    return (u'',) + tuple(filter(None, s.split(u'/')))

class DummyObjectMap:
    def __init__(self):
        self.added = []
        self.removed = []

    def add(self, obj, path, replace_oid=False):
        self.added.append((obj, path))
        objectid = getattr(obj, '__objectid__', None)
        if objectid is None:
            objectid = 1
            obj.__objectid__ = objectid
        return objectid

    def remove(self, objectid, references=True):
        self.references_removed = references
        self.removed.append(objectid)
        return [objectid]

class DummyEvent(object):
    def __init__(self, parent, moving=False, is_duplicated=False):
        self.parent = parent
        self.moving = moving
        self.is_duplicated = is_duplicated

class DummyTreeSet(set):
    def insert(self, val):
        self.add(val)

class DummyReferenceSet(object):
    def __init__(self, result=True):
        self.result = result
        self.connected = []
        self.disconnected = []

    def connect(self, src, target):
        self.connected.append((src, target))

    def disconnect(self, src, target):
        self.disconnected.append((src, target))

    def targetids(self, src):
        return self.result

    def sourceids(self, src):
        return self.result

class DummyReferenceMap(dict):
    def __init__(self, sourceids=(), targetids=()):
        self._sourceids = sourceids
        self._targetids = targetids
        
    def connect(self, src, target, reftype):
        self[reftype] = (src, target)

    def disconnect(self, src, target, reftype):
        del self[reftype]

    def sourceids(self, oid, reftype):
        return self._sourceids

    def targetids(self, oid, reftype):
        return self._targetids
    
def _makeSite(**kw):
    from ..interfaces import IFolder
    site = testing.DummyResource(__provides__=kw.pop('__provides__', None))
    alsoProvides(site, IFolder)
    services = testing.DummyResource()
    for k, v in kw.items():
        services[k] = v
    site['__services__'] = services
    return site

