import unittest

class Test_acl_modified(unittest.TestCase):
    def _callFUT(self, event):
        from ..subscribers import acl_modified
        return acl_modified(event)
    
    def test_it_no_objectmap(self):
        event = Dummy()
        event.object = Dummy()
        result = self._callFUT(event)
        self.assertEqual(result, None)

    def test_it_with_objectmap(self):

        acls = []

        def set_acl(obj, acl):
            acls.append((obj, acl))

        context = Dummy()
        context.__objectmap__ = Dummy()
        context.__objectmap__.set_acl = set_acl
        acl = [('Allow', 'fred', 'view')]
        event = Dummy()
        event.object = context
        event.new_acl = acl
        self._callFUT(event)

        self.assertEqual(acls, [(context, acl)])
    

class Dummy(object):
    pass
