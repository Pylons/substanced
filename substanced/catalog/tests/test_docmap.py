import unittest

class TestDocumentMap(unittest.TestCase):
    def _makeOne(self):
        from ..docmap import DocumentMap
        return DocumentMap()

    def test_new_docid(self):
        inst = self._makeOne()
        times = [0]
        def randrange(frm, to):
            val = times[0]
            times[0] = times[0] + 1
            return val
        inst._randrange = randrange
        inst.add((u'', 'whatever'), 0)
        self.assertEqual(inst.new_docid(), 1)

    def test_add_already_in_path_to_docid(self):
        inst = self._makeOne()
        inst.path_to_docid[(u'',)] = 1
        self.assertRaises(ValueError, inst.add, (u'',))

    def test_add_already_in_docid_to_path(self):
        inst = self._makeOne()
        inst.docid_to_path[1] = True
        self.assertRaises(ValueError, inst.add, (u'', u'a'), 1)

    def test_add_not_a_tuple(self):
        inst = self._makeOne()
        self.assertRaises(ValueError, inst.add, 'a')

    def test_remove_not_an_int_or_tuple(self):
        inst = self._makeOne()
        self.assertRaises(ValueError, inst.remove, 'a')

    def test_remove_no_dmap(self):
        inst = self._makeOne()
        inst.docid_to_path[1] = (u'',)
        result = inst.remove((u'',))
        self.assertEqual(list(result), [])

    def test_pathlookup_not_a_tuple(self):
        inst = self._makeOne()
        gen = inst.pathlookup(1)
        self.assertRaises(ValueError, list, gen)
        
    def test_functional(self):
    
        def split(s):
            return (u'',) + tuple(filter(None, s.split(u'/')))

        def l(path, depth=None, include_origin=True):
            path_tuple = split(path)
            return sorted(
                list(docmap.pathlookup(path_tuple, depth, include_origin))
                )

        docmap = self._makeOne()
        docmap._v_nextid = 1

        root = split('/')
        a = split('/a')
        ab = split('/a/b')
        abc = split('/a/b/c')
        z = split('/z')

        did1 = docmap.add(ab)
        did2 = docmap.add(abc)
        did3 = docmap.add(a)
        did4 = docmap.add(root)
        did5 = docmap.add(z)

        # /
        nodepth = l('/')
        assert nodepth == [did1, did2, did3, did4, did5], nodepth
        depth0 = l('/', depth=0)
        assert depth0 == [did4], depth0
        depth1 = l('/', depth=1)
        assert depth1 == [did3, did4, did5], depth1
        depth2 = l('/', depth=2)
        assert depth2 == [did1, did3, did4, did5], depth2
        depth3 = l('/', depth=3)
        assert depth3 == [did1, did2, did3, did4, did5], depth3
        depth4 = l('/', depth=4)
        assert depth4 == [did1, did2, did3, did4, did5], depth4

        # /a
        nodepth = l('/a')
        assert nodepth == [did1, did2, did3], nodepth
        depth0 = l('/a', depth=0)
        assert depth0 == [did3], depth0
        depth1 = l('/a', depth=1)
        assert depth1 == [did1, did3], depth1
        depth2 = l('/a', depth=2)
        assert depth2 == [did1, did2, did3], depth2
        depth3 = l('/a', depth=3)
        assert depth3 == [did1, did2, did3], depth3

        # /a/b
        nodepth = l('/a/b')
        assert nodepth == [did1, did2], nodepth
        depth0 = l('/a/b', depth=0)
        assert depth0 == [did1], depth0
        depth1 = l('/a/b', depth=1)
        assert depth1 == [did1, did2], depth1
        depth2 = l('/a/b', depth=2)
        assert depth2 == [did1, did2], depth2

        # /a/b/c
        nodepth = l('/a/b/c')
        assert nodepth == [did2], nodepth
        depth0 = l('/a/b/c', depth=0)
        assert depth0 == [did2], depth0
        depth1 = l('/a/b/c', depth=1)
        assert depth1 == [did2], depth1

        # remove '/a/b'
        removed = docmap.remove(did1)
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
        assert nodepth == [did3], nodepth
        depth0 = l('/a', depth=0)
        assert depth0 == [did3], depth0
        depth1 = l('/a', depth=1)
        assert depth1 == [did3], depth1

        # /
        nodepth = l('/')
        assert nodepth == [did3, did4, did5], nodepth
        depth0 = l('/', depth=0)
        assert depth0 == [did4], depth0
        depth1 = l('/', depth=1)
        assert depth1 == [did3, did4, did5], depth1

        # test include_origin false with /, no depth
        nodepth = l('/', include_origin=False)
        assert nodepth == [did3, did5], nodepth

        # test include_origin false with /, depth=1
        depth1 = l('/', include_origin=False, depth=0)
        assert depth1 == [], depth1
        
        pathindex = docmap.pathindex
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
            dict(docmap.docid_to_path),
            {3: (u'', u'a'), 4: (u'',), 5: (u'', u'z')})
        self.assertEqual(
            dict(docmap.path_to_docid),
            {(u'', u'z'): 5, (u'', u'a'): 3, (u'',): 4})

        # remove '/'
        removed = docmap.remove((u'',))
        self.assertEqual(removed, set([3,4,5]))

        assert dict(docmap.pathindex) == {}
        assert dict(docmap.docid_to_path) == {}
        assert dict(docmap.path_to_docid) == {}
