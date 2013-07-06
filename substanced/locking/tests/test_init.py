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
        from colander.iso8601 import UTC
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
    def _makeOne(self, timeout=3600, last_refresh=None):
        from .. import Lock
        return Lock(timeout=timeout, last_refresh=last_refresh)

    def test_ctor(self):
        inst = self._makeOne(5000, 1000)
        self.assertEqual(inst.timeout, 5000)
        self.assertEqual(inst.last_refresh, 1000)

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
        
class DummyUsers(object):
    def items(self):
        ob = testing.DummyResource()
        ob.__oid__ = 1
        yield 'name', ob
