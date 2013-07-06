import unittest

from pyramid import testing

class TestLockError(unittest.TestCase):
    def _makeOne(self, lock):
        from .. import LockError
        return LockError(lock)

    def test_ctor(self):
        inst = self._makeOne('lock')
        self.assertEqual(inst.lock, 'lock')
        
class TestUnlockError(unittest.TestCase):
    def _makeOne(self, lock):
        from .. import UnlockError
        return UnlockError(lock)

    def test_ctor(self):
        inst = self._makeOne('lock')
        self.assertEqual(inst.lock, 'lock')
        
        
class TestLock(unittest.TestCase):
    def _makeOne(self, timeout=3600):
        from .. import Lock
        return Lock(timeout=timeout)

    def test_ctor(self):
        inst = self._makeOne(5000)
        self.assertEqual(inst.timeout, 5000)
        self.assertTrue(inst.last_refresh)

    def test_refresh(self):
        import datetime
        inst = self._makeOne()
        now = datetime.datetime.utcnow()
        inst.refresh(when=now)
        self.assertEqual(inst.last_refresh, now)
        
    def test_refresh_with_timeout(self):
        import datetime
        inst = self._makeOne()
        now = datetime.datetime.utcnow()
        inst.refresh(timeout=30, when=now)
        self.assertEqual(inst.last_refresh, now)
        self.assertEqual(inst.timeout, 30)

    def test_expires_timeout_is_None(self):
        inst = self._makeOne()
        inst.timeout = None
        self.assertEqual(inst.expires(), None)
        
    def test_expires_timeout_is_int(self):
        import datetime
        inst = self._makeOne()
        inst.timeout = 30
        now = datetime.datetime.utcnow()
        inst.last_refresh = now
        self.assertEqual(inst.expires(), now + datetime.timedelta(seconds=30))

    def test_is_valid_expires_timeout_is_None(self):
        inst = self._makeOne()
        inst.timeout = None
        self.assertTrue(inst.is_valid())
        
    def test_is_valid_expires_timeout_is_int(self):
        import datetime
        inst = self._makeOne()
        inst.timeout = 30
        now = datetime.datetime.utcnow()
        future = now + datetime.timedelta(seconds=60)
        inst.last_refresh = now
        self.assertTrue(inst.is_valid(now))
        self.assertFalse(inst.is_valid(future))

    def test_is_valid_expires_resource_id_exists(self):
        import datetime
        inst = self._makeOne()
        inst.timeout = 30
        now = datetime.datetime.utcnow()
        inst.last_refresh = now
        inst.__objectmap__ = DummyObjectMap([1])
        self.assertTrue(inst.is_valid(now))

    def test_is_valid_expires_resource_id_notexist(self):
        import datetime
        inst = self._makeOne()
        inst.timeout = 30
        now = datetime.datetime.utcnow()
        inst.last_refresh = now
        inst.__objectmap__ = DummyObjectMap([])
        self.assertFalse(inst.is_valid(now))

    def test_commit_suicide(self):
        inst = self._makeOne()
        parent = testing.DummyResource()
        parent['foo'] = inst
        inst.commit_suicide()
        self.assertFalse('foo' in parent)
        
class DummyObjectMap(object):
    def __init__(self, result):
        self.result = result
    def sourceids(self, resource, reftype):
        return self.result
        
