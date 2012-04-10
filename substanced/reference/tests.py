import unittest

class TestReferenceSet(unittest.TestCase):
    def _makeOne(self):
        from . import ReferenceSet
        return ReferenceSet()

    def test_connect_empty(self):
        refset = self._makeOne()
        refset.connect(1, 2)
        self.assertEqual(list(refset.referents[1]), [2])
        self.assertEqual(list(refset.referrers[2]), [1])
        
    def test_connect_nonempty_overlap(self):
        refset = self._makeOne()
        refset.referents[1] = DummyOOTreeSet([2])
        refset.referrers[2] = DummyOOTreeSet([1])
        refset.connect(1, 2)
        self.assertEqual(list(refset.referents[1]), [2])
        self.assertEqual(list(refset.referrers[2]), [1])

    def test_connect_nonempty_nonoverlap(self):
        refset = self._makeOne()
        refset.referents[1] = DummyOOTreeSet([3])
        refset.referrers[2] = DummyOOTreeSet([4])
        refset.connect(1, 2)
        self.assertEqual(sorted(list(refset.referents[1])), [2, 3])
        self.assertEqual(sorted(list(refset.referrers[2])), [1, 4])

    def test_disconnect_empty(self):
        refset = self._makeOne()
        refset.disconnect(1, 2)
        self.assertEqual(list(refset.referents.keys()), [])
        self.assertEqual(list(refset.referrers.keys()), [])
        
    def test_disconnect_nonempty(self):
        refset = self._makeOne()
        refset.referents[1] = DummyOOTreeSet([2, 3])
        refset.referrers[2] = DummyOOTreeSet([1, 4])
        refset.disconnect(1, 2)
        self.assertEqual(list(refset.referents[1]), [3])
        self.assertEqual(list(refset.referrers[2]), [4])

    def test_disconnect_keyerrors(self):
        refset = self._makeOne()
        refset.referents[1] = DummyOOTreeSet()
        refset.referrers[2] = DummyOOTreeSet()
        refset.disconnect(1, 2)
        self.assertEqual(list(refset.referents[1]), [])
        self.assertEqual(list(refset.referrers[2]), [])

    def test_refers_to(self): 
        refset = self._makeOne()
        refset.referents[1] = DummyOOTreeSet([2])
        refset.referrers[2] = DummyOOTreeSet([1])
        self.assertEqual(refset.refers_to(1, 2), True)
        self.assertEqual(refset.refers_to(2, 1), False)
        self.assertEqual(refset.refers_to(1, 3), False)
       
    def test_referred_to(self): 
        refset = self._makeOne()
        refset.referents[1] = DummyOOTreeSet([2])
        refset.referrers[2] = DummyOOTreeSet([1])
        self.assertEqual(refset.referred_to(1, 2), False)
        self.assertEqual(refset.referred_to(2, 1), True)
        self.assertEqual(refset.referred_to(1, 3), False)

    def test_get_referents(self):
        refset = self._makeOne()
        dummyset = DummyOOTreeSet([1])
        refset.referents[1] = dummyset
        self.assertEqual(refset.get_referents(1), dummyset)
        
    def test_get_referrers(self):
        refset = self._makeOne()
        dummyset = DummyOOTreeSet(['a'])
        refset.referrers[1] = dummyset
        self.assertEqual(refset.get_referrers(1), dummyset)

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

    def test_refers_to_true(self):
        refset = DummyReferenceSet()
        map = {'reftype':refset}
        refs = self._makeOne(map)
        self.assertEqual(refs.refers_to('a', 'b', 'reftype'), True)

    def test_refers_to_no_such_refset(self):
        refs = self._makeOne()
        self.assertEqual(refs.refers_to('a', 'b', 'reftype'), False)

    def test_referred_to_true(self):
        refset = DummyReferenceSet()
        map = {'reftype':refset}
        refs = self._makeOne(map)
        self.assertEqual(refs.referred_to('a', 'b', 'reftype'), True)

    def test_referred_to_no_such_refset(self):
        refs = self._makeOne()
        self.assertEqual(refs.referred_to('a', 'b', 'reftype'), False)

    def test_get_referents_no_refset(self):
        refs = self._makeOne()
        self.assertEqual(refs.get_referents('a', 'reftype'), [])
        
    def test_get_referents_with_refset(self):
        refset = DummyReferenceSet(['123'])
        map = {'reftype':refset}
        refs = self._makeOne(map)
        self.assertEqual(refs.get_referents('a', 'reftype'), ['123'])

    def test_get_referers_no_refset(self):
        refs = self._makeOne()
        self.assertEqual(refs.get_referrers('a', 'reftype'), [])
        
    def test_get_referers_with_refset(self):
        refset = DummyReferenceSet(['123'])
        map = {'reftype':refset}
        refs = self._makeOne(map)
        self.assertEqual(refs.get_referrers('a', 'reftype'), ['123'])

class DummyOOTreeSet(set):
    def insert(self, val):
        self.add(val)
        
class DummyReferenceSet:
    def __init__(self, result=True):
        self.result = result
        self.connected = []
        self.disconnected = []

    def connect(self, src, target):
        self.connected.append((src, target))

    def disconnect(self, src, target):
        self.disconnected.append((src, target))

    def refers_to(self, src, target):
        return self.result

    def referred_to(self, src, target):
        return self.result

    def get_referents(self, src):
        return self.result

    def get_referrers(self, src):
        return self.result
    
    
    
