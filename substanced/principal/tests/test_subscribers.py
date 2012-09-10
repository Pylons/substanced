import unittest
from pyramid import testing

class Test_principal_added(unittest.TestCase):
    def _callFUT(self, event):
        from ..subscribers import principal_added
        return principal_added(event)

    def test_user_not_in_groups(self):
        from ...testing import make_site
        from ...interfaces import IUser
        site = make_site()
        user = testing.DummyResource(__provides__=IUser)
        site['user'] = user
        event = testing.DummyResource(object=user)
        self._callFUT(event) # doesnt blow up

    def test_user_in_groups(self):
        from ...testing import make_site
        from ...interfaces import IUser
        site = make_site()
        groups = site['__services__']['principals']['groups']
        groups['user'] = testing.DummyResource()
        user = testing.DummyResource(__provides__=IUser)
        site['user'] = user
        event = testing.DummyResource(object=user)
        self.assertRaises(ValueError, self._callFUT, event)

    def test_group_not_in_users(self):
        from ...testing import make_site
        site = make_site()
        group = testing.DummyResource()
        site['groups'] = group
        event = testing.DummyResource(object=group)
        self._callFUT(event) # doesnt blow up

    def test_group_in_users(self):
        from ...testing import make_site
        site = make_site()
        users = site['__services__']['principals']['users']
        users['group'] = testing.DummyResource()
        group = testing.DummyResource()
        site['group'] = group
        event = testing.DummyResource(object=group)
        self.assertRaises(ValueError, self._callFUT, event)

class Test_user_will_be_removed(unittest.TestCase):
    def _callFUT(self, event):
        from ..subscribers import user_will_be_removed
        return user_will_be_removed(event)

    def test_it(self):
        from ...interfaces import IFolder
        parent = testing.DummyResource(__provides__=IFolder)
        user = testing.DummyResource()
        reset = testing.DummyResource()
        def commit_suicide():
            reset.committed = True
        reset.commit_suicide = commit_suicide
        objectmap = DummyObjectMap((reset,))
        parent.__objectmap__ = objectmap
        parent['user'] = user
        event = testing.DummyResource(object=user)
        event.moving = False
        self._callFUT(event)
        self.assertTrue(reset.committed)

    def test_it_moving(self):
        event = testing.DummyResource(object=None)
        event.moving = True
        self.assertEqual(self._callFUT(event), None)

class Test_user_added(unittest.TestCase):
    def _callFUT(self, event):
        from ..subscribers import user_added
        return user_added(event)

    def test_it(self):
        from pyramid.security import Allow
        user = testing.DummyResource()
        user.__objectid__ = 1
        event = testing.DummyResource(object=user)
        self._callFUT(event)
        self.assertEqual(
            user.__acl__,
            [(Allow, 1, ('sdi.view', 'sdi.change-password'))]
            )

class DummyObjectMap(object):
    def __init__(self, result=()):
        self.result = result

    def targets(self, object, reftype):
        return self.result
    
