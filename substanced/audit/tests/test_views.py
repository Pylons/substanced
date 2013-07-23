import unittest
from pyramid import testing

class Test_AuditLogEventStreamView(unittest.TestCase):
    def _makeOne(self, context, request):
        from ..views import AuditLogEventStreamView
        view = AuditLogEventStreamView(context, request)
        view.logger = DummyLogger()
        return view

    def test_ctor(self):
        context = testing.DummyResource()
        request = testing.DummyRequest()
        inst = self._makeOne(context, request)
        self.assertEqual(inst.context, context)
        self.assertEqual(inst.request, request)

    def test_auditstream_sse_no_last_event_id(self):
        context = testing.DummyResource()
        request = testing.DummyRequest()
        request.GET = GetAllDict()
        inst = self._makeOne(context, request)
        inst.AuditScribe = DummyAuditScribe()
        response = inst.auditstream_sse()
        self.assertEqual(response.text, 'id: 0-1\ndata: \n\n')

    def test_auditstream_sse_with_last_event_id(self):
        context = testing.DummyResource()
        context.__oid__ = 5
        request = testing.DummyRequest()
        request.headers['Last-Event-Id'] = '1-1'
        request.GET = GetAllDict()
        inst = self._makeOne(context, request)
        inst.AuditScribe = DummyAuditScribe()
        response = inst.auditstream_sse()
        self.assertEqual(
            response.text,
            ('id: 0-1\nevent: smellin\ndata: payload1\n\n'
             'id: 0-2\nevent: smellin\ndata: payload2\n\n')
            )
        self.assertEqual(inst.AuditScribe.gen, 1)
        self.assertEqual(inst.AuditScribe.idx, 1) 
        self.assertEqual(inst.AuditScribe.oids, [5])

    def test_auditstream_sse_with_last_event_id_all(self):
        context = testing.DummyResource()
        context.__oid__ = 5
        request = testing.DummyRequest()
        request.headers['Last-Event-Id'] = '1-1'
        request.GET = GetAllDict()
        request.GET['all'] = '1'
        inst = self._makeOne(context, request)
        inst.AuditScribe = DummyAuditScribe()
        response = inst.auditstream_sse()
        self.assertEqual(
            response.text,
            ('id: 0-1\nevent: smellin\ndata: payload1\n\n'
             'id: 0-2\nevent: smellin\ndata: payload2\n\n')
            )
        self.assertEqual(inst.AuditScribe.gen, 1)
        self.assertEqual(inst.AuditScribe.idx, 1) 
        self.assertEqual(inst.AuditScribe.oids, ())
       
    def test_auditstream_sse_with_last_event_id_and_oids(self):
        context = testing.DummyResource()
        context.__oid__ = 5
        request = testing.DummyRequest()
        request.headers['Last-Event-Id'] = '1-1'
        request.GET = GetAllDict()
        request.GET['oid'] = '3'
        inst = self._makeOne(context, request)
        inst.AuditScribe = DummyAuditScribe()
        response = inst.auditstream_sse()
        self.assertEqual(
            response.text,
            ('id: 0-1\nevent: smellin\ndata: payload1\n\n'
             'id: 0-2\nevent: smellin\ndata: payload2\n\n')
            )
        self.assertEqual(inst.AuditScribe.gen, 1)
        self.assertEqual(inst.AuditScribe.idx, 1) 
        self.assertEqual(list(inst.AuditScribe.oids), [3])

    def test_auditing(self):
        import pytz
        context = testing.DummyResource()
        request = testing.DummyRequest()
        request.user = testing.DummyResource()
        request.user.timezone = pytz.timezone('UTC')
        inst = self._makeOne(context, request)
        inst.AuditScribe = DummyAuditScribe()
        result = inst.auditing()
        self.assertEqual(result['results'][0][0], 0)
        self.assertEqual(result['results'][0][1], 2)
        self.assertEqual(result['results'][0][2], '1970-01-01 00:00:01 UTC')
        self.assertEqual(result['results'][1][0], 0)
        self.assertEqual(result['results'][1][1], 1)
        self.assertEqual(result['results'][1][2], '1970-01-01 00:00:01 UTC')
        
class GetAllDict(dict):
    def getall(self, name): # pragma: no cover
        result = self.get(name)
        if result:
            return [result]
        return []

class DummyEvent(object):
    def __init__(self, payload):
        self.payload = payload
        self.name = 'smellin'
        self.timestamp = 1
        
class DummyAuditScribe(object):
    def __call__(self, context):
        self.context = context
        return self
    
    def latest_id(self):
        return 0, 1

    def __iter__(self):
        return iter(self.newer(0, 0))

    def newer(self, gen, idx, oids=()):
        self.gen = gen
        self.idx = idx
        self.oids = oids
        event1 = DummyEvent('payload1')
        event2 = DummyEvent('payload2')
        yield 0, 1, event1
        yield 0, 2, event2

class DummyLogger(object):
    def debug(self, msg):
        pass
