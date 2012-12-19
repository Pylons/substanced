import unittest
from pyramid import testing

class TestUndoViews(unittest.TestCase):
    def _makeOne(self, request):
        from ..undo import UndoViews
        return UndoViews(request)

    def test_undo_one_no_referrer(self):
        conn = DummyConnection()
        request = testing.DummyRequest()
        request._primary_zodb_conn = conn # XXX not an API, will break
        request.sdiapi = DummySDIAPI()
        request.referrer = None
        request.params['hash'] = 'hash'
        inst = self._makeOne(request)
        resp = inst.undo_one()
        self.assertEqual(resp.location, '/mgmt_path')
        
    def test_undo_one_with_referrer(self):
        conn = DummyConnection()
        request = testing.DummyRequest()
        request._primary_zodb_conn = conn # XXX not an API, will break
        request.sdiapi = DummySDIAPI()
        request.referrer = 'loc'
        request.params['hash'] = 'hash'
        inst = self._makeOne(request)
        resp = inst.undo_one()
        self.assertEqual(resp.location, 'loc')

    def test_undo_one_no_undo_info(self):
        conn = DummyConnection()
        request = testing.DummyRequest()
        request._primary_zodb_conn = conn # XXX not an API, will break
        request.sdiapi = DummySDIAPI()
        request.referrer = 'loc'
        request.params['hash'] = 'hash'
        inst = self._makeOne(request)
        inst.undo_one()
        self.assertEqual(request.session['_f_error'], ['Could not undo, sorry'])
        
    def test_undo_one_with_undo_info_no_match(self):
        record = {'description':'desc', 'id':'abc'}
        conn = DummyConnection(undo_info=[record])
        request = testing.DummyRequest()
        request._primary_zodb_conn = conn # XXX not an API, will break
        request.sdiapi = DummySDIAPI()
        request.referrer = 'loc'
        request.params['hash'] = 'hash'
        inst = self._makeOne(request)
        inst.undo_one()
        self.assertEqual(request.session['_f_error'], ['Could not undo, sorry'])

    def test_undo_one_with_undo_info_match(self):
        record = {'description':'hash:abc', 'id':'abc'}
        conn = DummyConnection(undo_info=[record])
        request = testing.DummyRequest()
        request._primary_zodb_conn = conn # XXX not an API, will break
        request.sdiapi = DummySDIAPI()
        request.referrer = 'loc'
        request.params['hash'] = 'abc'
        inst = self._makeOne(request)
        transaction = DummyTransaction()
        inst.transaction = transaction
        inst.undo_one()
        self.assertEqual(len(request.session['_f_success']), 1)
        self.assertEqual(len(conn._db.undone), 1)
        self.assertEqual(transaction.committed, True)

    def test_undo_one_with_undo_info_POSError(self):
        from ZODB.POSException import POSError
        record = {'description':'hash:abc', 'id':'abc'}
        conn = DummyConnection(undo_info=[record], undo_exc=POSError)
        request = testing.DummyRequest()
        request._primary_zodb_conn = conn # XXX not an API, will break
        request.sdiapi = DummySDIAPI()
        request.referrer = 'loc'
        request.params['hash'] = 'abc'
        transaction = DummyTransaction()
        inst = self._makeOne(request)
        inst.transaction = transaction
        inst.undo_one()
        self.assertEqual(len(request.session['_f_error']), 1)
        self.assertEqual(len(conn._db.undone), 0)
        self.assertEqual(transaction.aborted, True)

class DummyDB(object):
    def __init__(self, supports_undo, undo_info, undo_exc=None):
        self.supports_undo = supports_undo
        self.undo_info = undo_info
        self.undone = []
        self.undo_exc = undo_exc

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

class DummySDIAPI(object):
    def mgmt_path(self, *arg, **kw):
        return '/mgmt_path'

class DummyTransaction(object):
    def commit(self):
        self.committed = True

    def abort(self):
        self.aborted = True
        
