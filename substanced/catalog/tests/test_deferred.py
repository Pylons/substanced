import unittest
from pyramid import testing

class TestAction(unittest.TestCase):
    def _makeOne(self):
        from ..deferred import Action
        return Action()

    def test___repr__(self):
        inst = self._makeOne()
        result = repr(inst)
        self.assertTrue(
            result.startswith(
                '<substanced.catalog.deferred.Action object oid None for '
                'index None at')
            )

    def test___hash__(self):
        inst = self._makeOne()
        self.assertEqual(hash(inst), 1)

    def test___eq__True(self):
        inst = self._makeOne()
        other = self._makeOne()
        self.assertTrue(inst == other)

    def test___eq__False(self):
        inst = self._makeOne()
        other = self._makeOne()
        other.oid = 123
        self.assertFalse(inst == other)

    def test___lt__(self):
        inst = self._makeOne()
        other = self._makeOne()
        other.oid = 2
        inst.oid = 1
        self.assertTrue(inst < other)
        
    def test___gt__(self):
        # wrapped with total_ordering from functools, so this should work
        inst = self._makeOne()
        other = self._makeOne()
        other.oid = 2
        inst.oid = 1
        self.assertTrue(other.__gt__(inst))

class Test_pr_wrap(unittest.TestCase):
    def _callFUT(self, obj):
        from ..deferred import pr_wrap
        return pr_wrap(obj)

    def test_with_nonref(self):
        self.assertEqual(self._callFUT(1), 1)

    def test_with_ref(self):
        from ZODB.ConflictResolution import PersistentReference
        from ..deferred import PersistentReferenceProxy
        ref = PersistentReference((None, None))
        self.assertEqual(self._callFUT(ref).__class__, PersistentReferenceProxy)

class TestPersistentReferenceProxy(unittest.TestCase):
    def _makeOne(self, pr):
        from ..deferred import PersistentReferenceProxy
        return PersistentReferenceProxy(pr)

    def test___hash__(self):
        inst = self._makeOne(None)
        self.assertEqual(hash(inst), 1)

    def test___eq__True(self):
        inst1 = self._makeOne(None)
        inst2 = self._makeOne(None)
        self.assertTrue(inst1 == inst2)

    def test___eq__False(self):
        inst1 = self._makeOne(None)
        inst2 = self._makeOne(True)
        self.assertFalse(inst1 == inst2)
        
    def test___ne__True(self):
        inst1 = self._makeOne(None)
        inst2 = self._makeOne(True)
        self.assertTrue(inst1 != inst2)
        
    def test___ne__False(self):
        inst1 = self._makeOne(None)
        inst2 = self._makeOne(None)
        self.assertFalse(inst1 != inst2)

class TestIndexAction(unittest.TestCase):
    def _makeOne(self, index, mode='mode', oid='oid', resource='resource'):
        from ..deferred import IndexAction
        return IndexAction(index, mode, oid, resource)

    def test_execute(self):
        index = DummyIndex()
        inst = self._makeOne(index)
        inst.execute()
        self.assertEqual(index.oid, 'oid')
        self.assertEqual(index.resource, 'resource')
        self.assertEqual(inst.index, None)
        self.assertEqual(inst.oid, None)
        self.assertEqual(inst.resource, None)

class TestReindexAction(unittest.TestCase):
    def _makeOne(self, index, mode='mode', oid='oid', resource='resource'):
        from ..deferred import ReindexAction
        return ReindexAction(index, mode, oid, resource)

    def test_execute(self):
        index = DummyIndex()
        inst = self._makeOne(index)
        inst.execute()
        self.assertEqual(index.oid, 'oid')
        self.assertEqual(index.resource, 'resource')
        self.assertEqual(inst.index, None)
        self.assertEqual(inst.oid, None)
        self.assertEqual(inst.resource, None)

class TestUnindexAction(unittest.TestCase):
    def _makeOne(self, index, mode='mode', oid='oid'):
        from ..deferred import UnindexAction
        return UnindexAction(index, mode, oid)

    def test_execute(self):
        index = DummyIndex()
        inst = self._makeOne(index)
        inst.execute()
        self.assertEqual(index.oid, 'oid')
        self.assertEqual(inst.index, None)
        self.assertEqual(inst.oid, None)
        

class DummyIndex(object):
    def index_doc(self, oid, resource):
        self.oid = oid
        self.resource = resource

    reindex_doc = index_doc

    def unindex_doc(self, oid):
        self.oid = oid

