import unittest

from pyramid import testing

class Test_delete_locks(unittest.TestCase):
    def _callFUT(self, event):
        from ..subscribers import delete_locks
        return delete_locks(event)

    def test_event_moving(self):
        event = testing.DummyResource()
        event.loading = False
        event.moving = True
        result = self._callFUT(event)
        self.assertEqual(result, None)

    def test_event_loading(self):
        event = testing.DummyResource()
        event.loading = True
        event.moving = None
        result = self._callFUT(event)
        self.assertEqual(result, None)
        
    def test_objectmap_is_None(self):
        event = testing.DummyResource()
        event.moving = None
        event.loading = False
        event.object = None
        result = self._callFUT(event)
        self.assertEqual(result, None)

    def test_resource_is_IUser(self):
        from zope.interface import alsoProvides
        from substanced.interfaces import IUser
        event = testing.DummyResource()
        event.moving = None
        event.loading = False
        resource = testing.DummyResource()
        alsoProvides(resource, IUser)
        event.object = resource
        lock = testing.DummyResource()
        lock.suicided = 0
        def commit_suicide():
            lock.suicided+=1
        lock.commit_suicide = commit_suicide
        resource.__objectmap__ = DummyObjectMap([lock])
        result = self._callFUT(event)
        self.assertEqual(result, None)
        self.assertEqual(lock.suicided, 2)

    def test_resource_is_not_IUser(self):
        event = testing.DummyResource()
        event.moving = None
        event.loading = False
        resource = testing.DummyResource()
        event.object = resource
        lock = testing.DummyResource()
        lock.suicided = 0
        def commit_suicide():
            lock.suicided+=1
        lock.commit_suicide = commit_suicide
        resource.__objectmap__ = DummyObjectMap([lock])
        result = self._callFUT(event)
        self.assertEqual(result, None)
        self.assertEqual(lock.suicided, 1)
        
class DummyObjectMap(object):
    def __init__(self, result):
        self.result = result
    def targets(self, resource, type):
        return self.result

