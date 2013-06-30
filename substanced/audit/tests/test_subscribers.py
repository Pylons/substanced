import unittest
from pyramid import testing

class Test_aclchanged(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
        
    def _callFUT(self, event):
        from ..subscribers import acl_modified
        return acl_modified(event)

    def test_it(self):
        import json
        self.config.testing_securitypolicy('fred')
        event = Dummy()
        context = testing.DummyResource()
        context.__oid__ = 5
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
            {"old_acl": "old_acl", "new_acl": "new_acl", 'userid':'fred',
             'object_path':'/'}
            )
        
class Dummy(object):
    pass
