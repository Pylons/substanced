import json
import unittest
from pyramid import testing

class Test_acl_modified(unittest.TestCase):
    def setUp(self):
        self.request = testing.DummyRequest()
        self.config = testing.setUp(request=self.request)

    def tearDown(self):
        testing.tearDown()
        
    def _callFUT(self, event):
        from ..subscribers import acl_modified
        return acl_modified(event)

    def _makeRegistry(self):
        registry = Dummy()
        registry.content = DummyContentRegistry()
        return registry

    def test_it(self):
        self.request.user = Dummy({'__oid__':1, '__name__':'fred'})
        event = Dummy()
        context = testing.DummyResource()
        context.__oid__ = 5
        event.registry = self._makeRegistry()
        event.object = context
        event.old_acl = 'old_acl'
        event.new_acl = 'new_acl'
        self._callFUT(event)
        self.assertTrue(context.__auditlog__)
        entries = list(context.__auditlog__.entries)
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry[0], 0)
        self.assertEqual(entry[1], 0)
        self.assertEqual(entry[2].name, 'ACLModified')
        self.assertEqual(entry[2].oid, 5)
        self.assertEqual(
            json.loads(entry[2].payload),
            {
                'time':entry[2].timestamp,
                'old_acl': 'old_acl',
                'new_acl': 'new_acl',
                'userinfo':{'oid':1, 'name':'fred'},
                'object_path':'/',
                'content_type':'SteamingPile'
             }
            )

class Test_content_added_or_removed(unittest.TestCase):
    def setUp(self):
        self.request = testing.DummyRequest()
        self.config = testing.setUp(request=self.request)

    def tearDown(self):
        testing.tearDown()
        
    def _callFUT(self, event):
        from ..subscribers import content_added_or_removed
        return content_added_or_removed(event)

    def _makeRegistry(self):
        registry = Dummy()
        registry.content = DummyContentRegistry()
        return registry

    def test_event_is_not_added_or_removed_type(self):
        event = Dummy()
        result = self._callFUT(event)
        self.assertEqual(result, False)

    def _get_entries(self, event):
        event.parent = testing.DummyResource()
        event.parent.__oid__ = 10
        event.name = 'objectname'
        event.moving = False
        event.loading = False
        context = testing.DummyResource()
        context.__oid__ = 5
        event.registry = self._makeRegistry()
        event.object = context
        event.old_acl = 'old_acl'
        event.new_acl = 'new_acl'
        self._callFUT(event)
        self.assertTrue(context.__auditlog__)
        entries = list(context.__auditlog__.entries)
        return entries

    def test_it_removed(self):
        from substanced.interfaces import IObjectWillBeRemoved
        from zope.interface import alsoProvides
        self.request.user = Dummy({'__oid__':1, '__name__':'fred'})
        event = Dummy()
        alsoProvides(event, IObjectWillBeRemoved)
        entries = self._get_entries(event)
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry[0], 0)
        self.assertEqual(entry[1], 0)
        self.assertEqual(entry[2].name, 'ContentRemoved')
        self.assertEqual(entry[2].oid, 10)
        self.assertEqual(
            json.loads(entry[2].payload),
            {
                'folder_path': '/',
                'folder_oid': 10,
                'object_name': 'objectname',
                'moving': False,
                'loading': False,
                'userinfo': {'oid': 1, 'name': 'fred'},
                'content_type': 'SteamingPile',
                'time': entry[2].timestamp,
                'object_oid': 5

                }
            )

    def test_it_added(self):
        from substanced.interfaces import IObjectAdded
        from zope.interface import alsoProvides
        self.request.user = Dummy({'__oid__':1, '__name__':'fred'})
        event = Dummy()
        alsoProvides(event, IObjectAdded)
        entries = self._get_entries(event)
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry[0], 0)
        self.assertEqual(entry[1], 0)
        self.assertEqual(entry[2].name, 'ContentAdded')
        self.assertEqual(entry[2].oid, 10)
        self.assertEqual(
            json.loads(entry[2].payload),
            {
                'folder_path': '/',
                'folder_oid': 10,
                'object_name': 'objectname',
                'moving': False,
                'loading': False,
                'userinfo': {'oid': 1, 'name': 'fred'},
                'content_type': 'SteamingPile',
                'time': entry[2].timestamp,
                'object_oid': 5

                }
            )
        
class Test_content_modified(unittest.TestCase):
    def setUp(self):
        self.request = testing.DummyRequest()
        self.config = testing.setUp(request=self.request)

    def tearDown(self):
        testing.tearDown()
        
    def _callFUT(self, event):
        from ..subscribers import content_modified
        return content_modified(event)

    def _makeRegistry(self):
        registry = Dummy()
        registry.content = DummyContentRegistry()
        return registry

    def test_it(self):
        self.request.user = Dummy({'__oid__':1, '__name__':'fred'})
        event = Dummy()
        context = testing.DummyResource()
        context.__oid__ = 5
        event.registry = self._makeRegistry()
        event.object = context
        self._callFUT(event)
        self.assertTrue(context.__auditlog__)
        entries = list(context.__auditlog__.entries)
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry[0], 0)
        self.assertEqual(entry[1], 0)
        self.assertEqual(entry[2].name, 'ContentModified')
        self.assertEqual(entry[2].oid, 5)
        self.assertEqual(
            json.loads(entry[2].payload),
            {
                'object_oid': 5,
                'userinfo': {'oid': 1, 'name': 'fred'},
                'content_type': 'SteamingPile',
                'object_path': '/',
                'time': entry[2].timestamp,
                },
            )

class Dummy(object):
    def __init__(self, kw=None):
        if kw:
            self.__dict__.update(kw)

class DummyContentRegistry(object):
    def typeof(self, content):
        return 'SteamingPile'
    
