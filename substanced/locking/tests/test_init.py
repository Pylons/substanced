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

class Test_now(unittest.TestCase):
    def _callFUT(self):
        from .. import now
        return now()

    def test_it(self):
        from pytz import UTC
        result = self._callFUT()
        self.assertEqual(result.tzinfo, UTC)

class TestLockOwnerSchema(unittest.TestCase):
    def _makeOne(self):
        from .. import LockOwnerSchema
        return LockOwnerSchema()

    def test_widget(self):
        from zope.interface import alsoProvides
        from substanced.interfaces import IFolder
        inst = self._makeOne()
        resource = testing.DummyResource()
        alsoProvides(resource, IFolder)
        principals = testing.DummyResource()
        principals.__is_service__ = True
        resource['principals'] = principals
        principals['users'] = DummyUsers()
        inst.bindings = {}
        inst.bindings['context'] = resource
        widget = inst.widget
        self.assertEqual(widget.values, [(1, 'name')])

    def test_widget_principals_is_None(self):
        from zope.interface import alsoProvides
        from substanced.interfaces import IFolder
        inst = self._makeOne()
        resource = testing.DummyResource()
        alsoProvides(resource, IFolder)
        inst.bindings = {}
        inst.bindings['context'] = resource
        widget = inst.widget
        self.assertEqual(widget.values, [])

    def test_validator_success(self):
        inst = self._makeOne()
        resource = testing.DummyResource()
        resource.__objectmap__ = DummyObjectMap({1:True})
        inst.bindings = {}
        inst.bindings['context'] = resource
        result = inst.validator(None, 1)
        self.assertEqual(result, None) # doesnt raise

    def test_validator_failure(self):
        from colander import Invalid
        inst = self._makeOne()
        resource = testing.DummyResource()
        resource.__objectmap__ = DummyObjectMap({1:True})
        inst.bindings = {}
        inst.bindings['context'] = resource
        self.assertRaises(Invalid, inst.validator, None, 2)

class TestLockResourceSchema(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _makeOne(self):
        from .. import LockResourceSchema
        return LockResourceSchema()

    def test_preparer_value_is_path_allowed(self):
        self.config.testing_securitypolicy(permissive=True)
        inst = self._makeOne()
        resource = testing.DummyResource()
        resource.__objectmap__ = DummyObjectMap(resource)
        inst.bindings = {}
        inst.bindings['context'] = resource
        inst.bindings['request'] = testing.DummyRequest()
        result = inst.preparer('/abc/def')
        self.assertEqual(result, resource)

    def test_preparer_value_is_path_ValueError(self):
        self.config.testing_securitypolicy(permissive=True)
        inst = self._makeOne()
        resource = testing.DummyResource()
        resource.__objectmap__ = DummyObjectMap(resource, raises=ValueError)
        inst.bindings = {}
        inst.bindings['context'] = resource
        inst.bindings['request'] = testing.DummyRequest()
        result = inst.preparer('/abc/def')
        self.assertEqual(result, None)

    def test_preparer_value_is_path_not_allowed(self):
        self.config.testing_securitypolicy(permissive=False)
        inst = self._makeOne()
        resource = testing.DummyResource()
        resource.__objectmap__ = DummyObjectMap(resource)
        inst.bindings = {}
        inst.bindings['context'] = resource
        inst.bindings['request'] = testing.DummyRequest()
        result = inst.preparer('/abc/def')
        self.assertEqual(result, False)

    def test_preparer_value_is_colander_null(self):
        import colander
        self.config.testing_securitypolicy(permissive=True)
        inst = self._makeOne()
        resource = testing.DummyResource()
        resource.__objectmap__ = DummyObjectMap(resource)
        inst.bindings = {}
        inst.bindings['context'] = resource
        inst.bindings['request'] = testing.DummyRequest()
        result = inst.preparer(colander.null)
        self.assertEqual(result, colander.null)

    def test_validator_value_None(self):
        from colander import Invalid
        inst = self._makeOne()
        self.assertRaises(Invalid, inst.validator, None, None)

    def test_validator_value_False(self):
        from colander import Invalid
        inst = self._makeOne()
        self.assertRaises(Invalid, inst.validator, None, False)

    def test_validator_value_valid(self):
        inst = self._makeOne()
        result = inst.validator(None, 'valid')
        self.assertEqual(result, None) # doesnt raise

class TestLockPropertySheet(unittest.TestCase):
    def _makeOne(self, context, request):
        from .. import LockPropertySheet
        return LockPropertySheet(context, request)

    def test_get_resource_is_None(self):
        import colander
        context = testing.DummyResource()
        context.resource = None
        request = testing.DummyRequest()
        inst = self._makeOne(context, request)
        result = inst.get()
        self.assertEqual(result['resource'], colander.null)

    def test_get_resource_is_valid(self):
        context = testing.DummyResource()
        resource = testing.DummyResource()
        context.resource = resource
        request = testing.DummyRequest()
        inst = self._makeOne(context, request)
        result = inst.get()
        self.assertEqual(result['resource'], '/')

    def test_set_resource_is_null(self):
        import colander
        context = testing.DummyResource()
        request = testing.DummyRequest()
        inst = self._makeOne(context, request)
        inst.set({'resource':colander.null})
        self.assertEqual(context.resource, None)

    def test_set_resource_is_not_null(self):
        context = testing.DummyResource()
        request = testing.DummyRequest()
        inst = self._makeOne(context, request)
        inst.set({'resource':'abc'})
        self.assertEqual(context.resource, 'abc')

class TestLock(unittest.TestCase):
    def _makeOne(self, timeout=3600, comment=None, last_refresh=None):
        from .. import Lock
        return Lock(timeout=timeout, comment=comment, last_refresh=last_refresh)

    def test_ctor(self):
        inst = self._makeOne(5000, 'comment', 1000)
        self.assertEqual(inst.timeout, 5000)
        self.assertEqual(inst.last_refresh, 1000)
        self.assertEqual(inst.comment, 'comment')

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

class TestLockService(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _makeOne(self):
        from .. import LockService
        return LockService()

    def test_next_name(self):
        inst = self._makeOne()
        self.assertTrue(inst.next_name(None))

    def test__get_ownerid_object(self):
        resource = testing.DummyResource()
        resource.__oid__ = 1
        inst = self._makeOne()
        result = inst._get_ownerid(resource)
        self.assertEqual(result, 1)

    def test__get_ownerid_oid(self):
        inst = self._makeOne()
        result = inst._get_ownerid(1)
        self.assertEqual(result, 1)

    def test__get_ownerid_bogus(self):
        inst = self._makeOne()
        self.assertRaises(ValueError, inst._get_ownerid, 'bogus')

    def test_borrow_lock_without_existing_lock(self):
        inst = self._makeOne()
        inst.__objectmap__ = DummyObjectMap([])
        resource = testing.DummyResource()
        self.assertTrue(inst.borrow_lock(resource, 1) is None)

    def test_borrow_lock_with_invalid_existing_lock(self):
        inst = self._makeOne()
        lock = testing.DummyResource()
        def commit_suicide():
            lock.suicided = True
        lock.commit_suicide = commit_suicide
        lock.is_valid = lambda: False
        resource = testing.DummyResource()
        inst.__objectmap__ = DummyObjectMap([lock])
        self.config.registry.content = DummyContentRegistry(lock)
        self.assertTrue(inst.borrow_lock(resource, 1) is None)
        self.assertTrue(lock.suicided)

    def test_borrow_lock_with_valid_existing_lock_different_userid(self):
        from substanced.locking import LockError
        inst = self._makeOne()
        existing_lock = testing.DummyResource()
        existing_lock.ownerid = 2
        existing_lock.is_valid = lambda: True
        resource = testing.DummyResource()
        inst.__objectmap__ = DummyObjectMap([existing_lock])
        self.assertRaises(LockError, inst.borrow_lock, resource, 1)

    def test_borrow_lock_with_valid_existing_lock_same_userid(self):
        inst = self._makeOne()
        lock = testing.DummyResource()
        lock.ownerid = 1
        lock.is_valid = lambda: True
        lock.timeout = None
        def refresh(timeout, when): #pragma NO COVER
            lock.timeout = timeout
        lock.refresh = refresh
        resource = testing.DummyResource()
        inst.__objectmap__ = DummyObjectMap([lock])
        result = inst.borrow_lock(resource, 1)
        self.assertEqual(result.timeout, None)

    def test_lock_without_existing_lock(self):
        inst = self._makeOne()
        lock = testing.DummyResource()
        resource = testing.DummyResource()
        self.config.registry.content = DummyContentRegistry(lock)
        inst.__objectmap__ = DummyObjectMap([])
        result = inst.lock(resource, 1)
        self.assertEqual(result, lock)
        self.assertEqual(result.ownerid, 1)
        self.assertEqual(result.resource, resource)

    def test_lock_with_invalid_existing_lock(self):
        inst = self._makeOne()
        lock = testing.DummyResource()
        def commit_suicide():
            lock.suicided = True
        lock.commit_suicide = commit_suicide
        lock.is_valid = lambda: False
        resource = testing.DummyResource()
        inst.__objectmap__ = DummyObjectMap([lock])
        self.config.registry.content = DummyContentRegistry(lock)
        result = inst.lock(resource, 1)
        self.assertEqual(result, lock)
        self.assertEqual(result.ownerid, 1)
        self.assertEqual(result.resource, resource)
        self.assertTrue(lock.suicided)

    def test_lock_with_valid_existing_lock_different_userid(self):
        from substanced.locking import LockError
        inst = self._makeOne()
        existing_lock = testing.DummyResource()
        existing_lock.ownerid = 2
        existing_lock.is_valid = lambda: True
        resource = testing.DummyResource()
        inst.__objectmap__ = DummyObjectMap([existing_lock])
        self.assertRaises(LockError, inst.lock, resource, 1)

    def test_lock_with_valid_existing_lock_same_userid(self):
        inst = self._makeOne()
        lock = testing.DummyResource()
        lock.ownerid = 1
        lock.is_valid = lambda: True
        def refresh(timeout, when):
            lock.timeout = timeout
            lock.when = when
        lock.refresh = refresh
        resource = testing.DummyResource()
        inst.__objectmap__ = DummyObjectMap([lock])
        result = inst.lock(resource, 1, timeout=3600)
        self.assertEqual(result.timeout, 3600)
        self.assertTrue(result.when)

    def test_unlock_without_existing_lock(self):
        from substanced.locking import UnlockError
        inst = self._makeOne()
        resource = testing.DummyResource()
        inst.__objectmap__ = DummyObjectMap([])
        self.assertRaises(UnlockError, inst.unlock, resource, 1)

    def test_unlock_with_invalid_existing_lock(self):
        inst = self._makeOne()
        lock = testing.DummyResource()
        lock.ownerid = 1
        lock.is_valid = lambda: False
        def commit_suicide():
            lock.suicided = True
        lock.commit_suicide = commit_suicide
        resource = testing.DummyResource()
        inst.__objectmap__ = DummyObjectMap([lock])
        inst.unlock(resource, 1)
        self.assertTrue(lock.suicided)

    def test_unlock_with_valid_existing_lock_same_userid(self):
        inst = self._makeOne()
        lock = testing.DummyResource()
        lock.ownerid = 1
        lock.is_valid = lambda: True
        def commit_suicide():
            lock.suicided = True
        lock.commit_suicide = commit_suicide
        resource = testing.DummyResource()
        inst.__objectmap__ = DummyObjectMap([lock])
        inst.unlock(resource, 1)
        self.assertTrue(lock.suicided)

    def test_discover_filter_invalid(self):
        inst = self._makeOne()
        lock1 = testing.DummyResource()
        lock1.is_valid = lambda: True
        lock2 = testing.DummyResource()
        lock2.is_valid = lambda: False
        inst.__objectmap__ = DummyObjectMap([lock1, lock2])
        result = inst.discover(None)
        self.assertEqual(result, [lock1])

    def test_discover_invalid_not_filtered_when_include_invalid(self):
        inst = self._makeOne()
        lock1 = testing.DummyResource()
        lock1.is_valid = lambda: True
        lock2 = testing.DummyResource()
        lock2.is_valid = lambda: False
        inst.__objectmap__ = DummyObjectMap([lock1, lock2])
        result = inst.discover(None, include_invalid=True)
        self.assertEqual(result, [lock1, lock2])

class Test_lock_resource(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _callFUT(self, resource, owner_or_ownerid, timeout=None):
        from substanced.locking import lock_resource
        return lock_resource(resource, owner_or_ownerid, timeout=timeout)

    def test_it_with_existing_lock_service(self):
        from substanced.locking import WriteLock
        from zope.interface import alsoProvides
        from substanced.interfaces import IFolder
        resource = testing.DummyResource()
        alsoProvides(resource, IFolder)
        lockservice = DummyLockService()
        resource['locks'] = lockservice
        result = self._callFUT(resource, 1, 3600)
        self.assertEqual(result, True)
        self.assertEqual(lockservice.resource, resource)
        self.assertEqual(lockservice.owner, 1)
        self.assertEqual(lockservice.timeout, 3600)
        self.assertEqual(lockservice.locktype, WriteLock)

    def test_it_with_missing_lock_service(self):
        from substanced.locking import WriteLock
        from zope.interface import alsoProvides
        from substanced.interfaces import IFolder
        lockservice = DummyLockService()
        self.config.registry.content = DummyContentRegistry(lockservice)
        resource = testing.DummyResource()
        resource.add_service = resource.__setitem__
        alsoProvides(resource, IFolder)
        result = self._callFUT(resource, 1, 3600)
        self.assertEqual(result, True)
        self.assertEqual(resource['locks'], lockservice)
        self.assertEqual(lockservice.resource, resource)
        self.assertEqual(lockservice.owner, 1)
        self.assertEqual(lockservice.timeout, 3600)
        self.assertEqual(lockservice.locktype, WriteLock)

class Test_could_lock_resource(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _callFUT(self, resource, owner_or_ownerid):
        from substanced.locking import could_lock_resource
        return could_lock_resource(resource, owner_or_ownerid)

    def test_it_with_existing_lock_service(self):
        from zope.interface import alsoProvides
        from substanced.interfaces import IFolder
        resource = testing.DummyResource()
        alsoProvides(resource, IFolder)
        lockservice = DummyLockService()
        resource['locks'] = lockservice
        result = self._callFUT(resource, 1)
        self.assertEqual(result, True)
        self.assertEqual(lockservice.borrowed, resource)

    def test_it_with_missing_lock_service(self):
        from zope.interface import alsoProvides
        from substanced.interfaces import IFolder
        lockservice = DummyLockService()
        self.config.registry.content = DummyContentRegistry(lockservice)
        resource = testing.DummyResource()
        resource.add_service = resource.__setitem__
        alsoProvides(resource, IFolder)
        result = self._callFUT(resource, 1)
        self.assertEqual(result, True)
        self.assertEqual(resource['locks'], lockservice)
        self.assertEqual(lockservice.borrowed, resource)

class Test_unlock_resource(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _callFUT(self, resource, owner_or_ownerid):
        from substanced.locking import unlock_resource
        return unlock_resource(resource, owner_or_ownerid)

    def test_it_with_existing_lock_service(self):
        from substanced.locking import WriteLock
        from zope.interface import alsoProvides
        from substanced.interfaces import IFolder
        resource = testing.DummyResource()
        alsoProvides(resource, IFolder)
        lockservice = DummyLockService()
        resource['locks'] = lockservice
        result = self._callFUT(resource, 1)
        self.assertEqual(result, True)
        self.assertEqual(lockservice.resource, resource)
        self.assertEqual(lockservice.owner, 1)
        self.assertEqual(lockservice.locktype, WriteLock)

    def test_it_with_missing_lock_service(self):
        from substanced.locking import WriteLock
        from zope.interface import alsoProvides
        from substanced.interfaces import IFolder
        lockservice = DummyLockService()
        self.config.registry.content = DummyContentRegistry(lockservice)
        resource = testing.DummyResource()
        resource.add_service = resource.__setitem__
        alsoProvides(resource, IFolder)
        result = self._callFUT(resource, 1)
        self.assertEqual(result, True)
        self.assertEqual(resource['locks'], lockservice)
        self.assertEqual(lockservice.resource, resource)
        self.assertEqual(lockservice.owner, 1)
        self.assertEqual(lockservice.locktype, WriteLock)

class Test_discover_resource_locks(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _callFUT(self, resource):
        from substanced.locking import discover_resource_locks
        return discover_resource_locks(resource)

    def test_it_with_existing_lock_service(self):
        from substanced.locking import WriteLock
        from zope.interface import alsoProvides
        from substanced.interfaces import IFolder
        resource = testing.DummyResource()
        alsoProvides(resource, IFolder)
        lockservice = DummyLockService()
        resource['locks'] = lockservice
        result = self._callFUT(resource)
        self.assertEqual(result, True)
        self.assertEqual(lockservice.resource, resource)
        self.assertEqual(lockservice.locktype, WriteLock)

    def test_it_with_missing_lock_service(self):
        from substanced.locking import WriteLock
        from zope.interface import alsoProvides
        from substanced.interfaces import IFolder
        lockservice = DummyLockService()
        self.config.registry.content = DummyContentRegistry(lockservice)
        resource = testing.DummyResource()
        resource.add_service = resource.__setitem__
        alsoProvides(resource, IFolder)
        result = self._callFUT(resource)
        self.assertEqual(result, True)
        self.assertEqual(resource['locks'], lockservice)
        self.assertEqual(lockservice.resource, resource)
        self.assertEqual(lockservice.locktype, WriteLock)

class DummyObjectMap(object):
    def __init__(self, result, raises=None):
        self.result = result
        self.raises = raises
    def sourceids(self, resource, reftype):
        return self.result
    @property
    def objectid_to_path(self):
        return self.result
    def object_for(self, value):
        if self.raises is not None:
            raise self.raises
        return self.result
    def targets(self, resource, type):
        return self.result
    def add(self, *arg, **kw):
        self.added = True

class DummyContentRegistry(object):
    def __init__(self, result):
        self.result = result

    def create(self, *arg, **kw):
        return self.result

class DummyUsers(object):
    def items(self):
        ob = testing.DummyResource()
        ob.__oid__ = 1
        yield 'name', ob

class DummyLockService(object):
    __is_service__ = True
    def lock(self, resource, owner, timeout=None, comment=None, locktype=None):
        self.resource = resource
        self.owner = owner
        self.timeout = timeout
        self.comment = comment
        self.locktype = locktype
        return True

    def borrow_lock(self, resource, owner, locktype=None):
        self.borrowed = resource
        return True

    unlock = lock

    def discover(self, resource, include_invalid=False, locktype=None):
        self.resource = resource
        self.locktype = locktype
        return True
