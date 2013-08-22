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
        from substanced.audit import AuditLog
        self.request.user = Dummy({'__oid__':1, '__name__':'fred'})
        event = Dummy()
        context = testing.DummyResource()
        context.__auditlog__ = AuditLog()
        context.__oid__ = 5
        event.registry = self._makeRegistry()
        event.object = context
        event.old_acl = 'old_acl'
        event.new_acl = 'new_acl'
        self._callFUT(event)
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

    def test_it_noscribe(self):
        event = Dummy()
        context = testing.DummyResource()
        context.__oid__ = 5
        event.object = context
        self.assertEqual(self._callFUT(event), None)

_marker = object()

class Test_content_added_moved_or_duplicated(unittest.TestCase):
    def setUp(self):
        self.request = testing.DummyRequest()
        self.config = testing.setUp(request=self.request)

    def tearDown(self):
        testing.tearDown()
        
    def _callFUT(self, event):
        from ..subscribers import content_added_moved_or_duplicated
        return content_added_moved_or_duplicated(event)

    def _makeRegistry(self):
        registry = Dummy()
        registry.content = DummyContentRegistry()
        return registry

    def _get_entries(self, event, auditlog=_marker):
        from substanced.audit import AuditLog
        event.parent = testing.DummyResource()
        if auditlog is _marker:
            auditlog = AuditLog()
        event.parent.__auditlog__ = auditlog
        event.parent.__oid__ = 10
        event.name = 'objectname'
        context = testing.DummyResource()
        context.__oid__ = 5
        context.__parent__ = event.parent
        event.registry = self._makeRegistry()
        event.object = context
        event.old_acl = 'old_acl'
        event.new_acl = 'new_acl'
        self._callFUT(event)
        if auditlog:
            entries = list(event.parent.__auditlog__.entries)
            return entries

    def test_it_added(self):
        self.request.user = Dummy({'__oid__':1, '__name__':'fred'})
        event = Dummy()
        event.moving = None
        event.duplicating = None
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
                'userinfo': {'oid': 1, 'name': 'fred'},
                'content_type': 'SteamingPile',
                'time': entry[2].timestamp,
                'object_oid': 5

                }
            )

    def test_it_added_noscribe(self):
        event = Dummy()
        event.moving = None
        event.duplicating = None
        entries = self._get_entries(event, None)
        self.assertEqual(entries, None)
        
    def test_it_moved(self):
        self.request.user = Dummy({'__oid__':1, '__name__':'fred'})
        event = Dummy()
        event.moving = True
        event.duplicating = None
        entries = self._get_entries(event)
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry[0], 0)
        self.assertEqual(entry[1], 0)
        self.assertEqual(entry[2].name, 'ContentMoved')
        self.assertEqual(entry[2].oid, 10)
        self.assertEqual(
            json.loads(entry[2].payload),
            {
                'folder_path': '/',
                'folder_oid': 10,
                'object_name': 'objectname',
                'userinfo': {'oid': 1, 'name': 'fred'},
                'content_type': 'SteamingPile',
                'time': entry[2].timestamp,
                'object_oid': 5

                }
            )

    def test_it_duplicated(self):
        self.request.user = Dummy({'__oid__':1, '__name__':'fred'})
        event = Dummy()
        event.moving = None
        event.duplicating = True
        entries = self._get_entries(event)
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry[0], 0)
        self.assertEqual(entry[1], 0)
        self.assertEqual(entry[2].name, 'ContentDuplicated')
        self.assertEqual(entry[2].oid, 10)
        self.assertEqual(
            json.loads(entry[2].payload),
            {
                'folder_path': '/',
                'folder_oid': 10,
                'object_name': 'objectname',
                'userinfo': {'oid': 1, 'name': 'fred'},
                'content_type': 'SteamingPile',
                'time': entry[2].timestamp,
                'object_oid': 5

                }
            )
        
class Test_content_removed(unittest.TestCase):
    def setUp(self):
        self.request = testing.DummyRequest()
        self.config = testing.setUp(request=self.request)

    def tearDown(self):
        testing.tearDown()
        
    def _callFUT(self, event):
        from ..subscribers import content_removed
        return content_removed(event)
    
    def _makeRegistry(self):
        registry = Dummy()
        registry.content = DummyContentRegistry()
        return registry

    def _get_entries(self, event):
        from substanced.audit import AuditLog
        event.parent = testing.DummyResource()
        event.parent.__auditlog__ = AuditLog()
        event.parent.__oid__ = 10
        event.name = 'objectname'
        context = testing.DummyResource()
        context.__oid__ = 5
        context.__parent__ = event.parent
        event.registry = self._makeRegistry()
        event.object = context
        event.old_acl = 'old_acl'
        event.new_acl = 'new_acl'
        self._callFUT(event)
        entries = list(event.parent.__auditlog__.entries)
        return entries

    def test_it_moving(self):
        event = Dummy()
        event.moving = True
        self.assertEqual(self._callFUT(event), None)

    def test_it(self):
        self.request.user = Dummy({'__oid__':1, '__name__':'fred'})
        event = Dummy()
        event.moving = None
        event.duplicating = None
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

    def test_it_noscribe(self):
        event = Dummy()
        context = testing.DummyResource()
        event.object = context
        self.assertEqual(self._callFUT(event), None)
        
    def test_it(self):
        from substanced.audit import AuditLog
        self.request.user = Dummy({'__oid__':1, '__name__':'fred'})
        event = Dummy()
        context = testing.DummyResource()
        context.__oid__ = 5
        context.__auditlog__ = AuditLog()
        event.registry = self._makeRegistry()
        event.object = context
        self._callFUT(event)
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

class Test_logged_in(unittest.TestCase):
    def setUp(self):
        self.request = testing.DummyRequest()
        self.config = testing.setUp(request=self.request)

    def tearDown(self):
        testing.tearDown()
        
    def _callFUT(self, event):
        from ..subscribers import logged_in
        return logged_in(event)

    def test_it_noscribe(self):
        event = Dummy()
        event.request = Dummy()
        context = testing.DummyResource()
        event.request.context = context
        self.assertEqual(self._callFUT(event), None)

    def test_it_user_has_oid(self):
        from substanced.audit import AuditLog
        event = Dummy()
        event.request = Dummy()
        context = testing.DummyResource()
        context.__auditlog__ = AuditLog()
        event.request.context = context
        user = Dummy()
        user.__oid__ = 5
        event.user = user
        event.login = 'login'
        self._callFUT(event)
        entries = list(context.__auditlog__.entries)
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry[0], 0)
        self.assertEqual(entry[1], 0)
        self.assertEqual(entry[2].name, 'LoggedIn')
        self.assertEqual(entry[2].oid, None)
        self.assertEqual(
            json.loads(entry[2].payload),
            {
                'user_oid': 5,
                'login': 'login',
                'time': entry[2].timestamp,
                },
            )

    def test_it_user_has_no_oid(self):
        from substanced.audit import AuditLog
        event = Dummy()
        event.request = Dummy()
        context = testing.DummyResource()
        context.__auditlog__ = AuditLog()
        event.request.context = context
        user = Dummy()
        event.user = user
        event.login = 'login'
        self._callFUT(event)
        entries = list(context.__auditlog__.entries)
        self.assertEqual(len(entries), 1)
        entry = entries[0]
        self.assertEqual(entry[0], 0)
        self.assertEqual(entry[1], 0)
        self.assertEqual(entry[2].name, 'LoggedIn')
        self.assertEqual(entry[2].oid, None)
        self.assertEqual(
            json.loads(entry[2].payload),
            {
                'user_oid': None,
                'login': 'login',
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
    
