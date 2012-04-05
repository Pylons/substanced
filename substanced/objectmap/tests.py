import unittest
from pyramid import testing

class TestObjectMap(unittest.TestCase):
    def _makeOne(self):
        from . import ObjectMap
        site = testing.DummyResource()
        return ObjectMap(site)

    def test_new_objectid_empty(self):
        inst = self._makeOne()
        times = [0]
        def randrange(frm, to):
            val = times[0]
            times[0] = times[0] + 1
            return val
        inst._randrange = randrange
        result = inst.new_objectid()
        self.assertEqual(result, 0)
        
    def test_new_objectid_notempty(self):
        inst = self._makeOne()
        times = [0]
        def randrange(frm, to):
            val = times[0]
            times[0] = times[0] + 1
            return val
        inst._randrange = randrange
        inst.objectid_to_path[0] = True
        result = inst.new_objectid()
        self.assertEqual(result, 1)

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
        
    def test_add_already_in_path_to_objectid(self):
        inst = self._makeOne()
        obj = testing.DummyResource()
        obj.__objectid__ = 1
        inst.path_to_objectid[(u'',)] = 1
        self.assertRaises(ValueError, inst.add, obj)

    def test_add_already_in_objectid_to_path(self):
        inst = self._makeOne()
        obj = testing.DummyResource()
        obj.__objectid__ = 1
        inst.objectid_to_path[1] = True
        self.assertRaises(ValueError, inst.add, obj)

    def test_add_traversable_object(self):
        inst = self._makeOne()
        inst._v_nextid = 1
        obj = testing.DummyResource()
        inst.add(obj)
        self.assertEqual(inst.objectid_to_path[1], (u'',))
        self.assertEqual(obj.__objectid__, 1)
        
    def test_add_not_valid(self):
        inst = self._makeOne()
        self.assertRaises(ValueError, inst.add, 'a')

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
            inst.add(thing)
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
            inst.add(thing)
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
            inst.add(thing)
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
            inst.add(thing)
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
            inst.add(thing)
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
            inst.add(thing)
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

        oid1 = objmap.add(ab)
        oid2 = objmap.add(abc)
        oid3 = objmap.add(a)
        oid4 = objmap.add(root)
        oid5 = objmap.add(z)

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

def resource(path):
    path_tuple = split(path)
    parent = None
    for element in path_tuple:
        obj = testing.DummyResource()
        obj.__parent__ = parent
        obj.__name__ = element
        parent = obj
    return obj
                
        
def split(s):
    return (u'',) + tuple(filter(None, s.split(u'/')))

