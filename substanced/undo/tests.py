import unittest
from pyramid import testing

class TestFlashUndo(unittest.TestCase):
    def setUp(self):
        self.config = testing.setUp()

    def tearDown(self):
        testing.tearDown()
        
    def _makeOne(self, request):
        from . import FlashUndo
        return FlashUndo(request)

    def test_no_permission(self):
        self.config.testing_securitypolicy(permissive=False)
        request = testing.DummyRequest()
        inst = self._makeOne(request)
        connection = DummyConnection()
        inst.get_connection = lambda *arg: connection
        inst.transaction = DummyTransaction()
        inst('message')
        self.assertEqual(request.session['_f_'], ['message'])
        self.assertFalse(inst.transaction.notes)

    def test_db_doesnt_support_undo(self):
        self.config.testing_securitypolicy(permissive=True)
        request = testing.DummyRequest()
        inst = self._makeOne(request)
        connection = DummyConnection(supports_undo=False)
        inst.get_connection = lambda *arg: connection
        inst.transaction = DummyTransaction()
        inst('message')
        self.assertEqual(request.session['_f_'], ['message'])
        self.assertFalse(inst.transaction.notes)

    def test_it(self):
        self.config.testing_securitypolicy(permissive=True)
        request = testing.DummyRequest()
        request.mgmt_path = lambda *arg, **kw: '/mg'
        inst = self._makeOne(request)
        connection = DummyConnection()
        inst.get_connection = lambda *arg: connection
        inst.transaction = DummyTransaction()
        inst('message')
        self.assertEqual(request.session['_f_'],
                         [u'<span>message <a href="/mg" class="btn btn-mini '
                          u'btn-info">Undo</a></span>\n'])
        self.assertTrue(inst.transaction.notes)

class DummyTransaction(object):
    def __init__(self):
        self.notes = []
        
    def get(self):
        return self

    def note(self, note):
        self.notes.append(note)

class DummyDB(object):
    def __init__(self, supports_undo):
        self.supports_undo = supports_undo

    def supportsUndo(self):
        return self.supports_undo
        
class DummyConnection(object):
    def __init__(self, supports_undo=True):
        self._db = DummyDB(supports_undo)

    def db(self):
        return self._db
        
