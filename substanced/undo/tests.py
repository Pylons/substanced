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

class Test_undo_one(unittest.TestCase):
    def _callFUT(self, request):
        from . import undo_one
        return undo_one(request)

    def test_no_referrer(self):
        conn = DummyConnection()
        request = testing.DummyRequest()
        request._primary_zodb_conn = conn # XXX not an API, will break
        request.mgmt_path = lambda *arg: '/mgmt'
        request.referrer = None
        request.params['hash'] = 'hash'
        resp = self._callFUT(request)
        self.assertEqual(resp.location, '/mgmt')
        
    def test_with_referrer(self):
        conn = DummyConnection()
        request = testing.DummyRequest()
        request._primary_zodb_conn = conn # XXX not an API, will break
        request.mgmt_path = lambda *arg: '/mgmt'
        request.referrer = 'loc'
        request.params['hash'] = 'hash'
        resp = self._callFUT(request)
        self.assertEqual(resp.location, 'loc')

    def test_no_undo_info(self):
        conn = DummyConnection()
        request = testing.DummyRequest()
        request._primary_zodb_conn = conn # XXX not an API, will break
        request.mgmt_path = lambda *arg: '/mgmt'
        request.referrer = 'loc'
        request.params['hash'] = 'hash'
        self._callFUT(request)
        self.assertEqual(request.session['_f_error'], ['Could not undo, sorry'])
        
    def test_with_undo_info_no_match(self):
        record = {'description':'desc', 'id':'abc'}
        conn = DummyConnection(undo_info=[record])
        request = testing.DummyRequest()
        request._primary_zodb_conn = conn # XXX not an API, will break
        request.mgmt_path = lambda *arg: '/mgmt'
        request.referrer = 'loc'
        request.params['hash'] = 'hash'
        self._callFUT(request)
        self.assertEqual(request.session['_f_error'], ['Could not undo, sorry'])

    def test_with_undo_info_match(self):
        record = {'description':'hash:abc', 'id':'abc'}
        conn = DummyConnection(undo_info=[record])
        request = testing.DummyRequest()
        request._primary_zodb_conn = conn # XXX not an API, will break
        request.mgmt_path = lambda *arg: '/mgmt'
        request.referrer = 'loc'
        request.params['hash'] = 'abc'
        self._callFUT(request)
        self.assertEqual(len(request.session['_f_success']), 1)
        self.assertEqual(len(conn._db.undone), 1)

    def test_with_undo_info_POSError(self):
        from ZODB.POSException import POSError
        record = {'description':'hash:abc', 'id':'abc'}
        conn = DummyConnection(undo_info=[record], undo_exc=POSError)
        request = testing.DummyRequest()
        request._primary_zodb_conn = conn # XXX not an API, will break
        request.mgmt_path = lambda *arg: '/mgmt'
        request.referrer = 'loc'
        request.params['hash'] = 'abc'
        self._callFUT(request)
        self.assertEqual(len(request.session['_f_error']), 1)
        self.assertEqual(len(conn._db.undone), 0)

class DummyTransaction(object):
    def __init__(self):
        self.notes = []
        
    def get(self):
        return self

    def note(self, note):
        self.notes.append(note)

class DummyDB(object):
    def __init__(self, supports_undo, undo_info, undo_exc=None):
        self.supports_undo = supports_undo
        self.undo_info = undo_info
        self.undone = []
        self.undo_exc = undo_exc

    def supportsUndo(self):
        return self.supports_undo

    def undoInfo(self):
        return self.undo_info

    def undo(self, id):
        if self.undo_exc:
            raise self.undo_exc
        self.undone.append(id)
        
class DummyConnection(object):
    def __init__(self, supports_undo=True, undo_info=(), undo_exc=None):
        self._db = DummyDB(supports_undo, undo_info, undo_exc)

    def db(self):
        return self._db

