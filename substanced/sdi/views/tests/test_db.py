import unittest
from pyramid import testing

class TestManageDatabase(unittest.TestCase):
    def _makeOne(self, context, request):
        from ..db import ManageDatabase
        return ManageDatabase(context, request)

    def test_view_with_activity_monitor(self):
        context = testing.DummyResource()
        request = testing.DummyRequest()
        inst = self._makeOne(context, request)
        am = DummyActivityMonitor()
        conn = DummyConnection(am=am)
        inst.get_connection = lambda *arg: conn
        result = inst.view()
        self.assertEqual(result['data_connections'], '[[1000, 1], [1000, 1]]')
        self.assertEqual(result['data_object_loads'], '[[1000, 1], [1000, 1]]')
        self.assertEqual(result['data_object_stores'], '[[1000, 1], [1000, 1]]')

    def test_view_no_activity_monitor(self):
        context = testing.DummyResource()
        request = testing.DummyRequest()
        inst = self._makeOne(context, request)
        conn = DummyConnection(am=None)
        inst.get_connection = lambda *arg: conn
        result = inst.view()
        self.assertEqual(result['data_connections'], '[]')
        self.assertEqual(result['data_object_loads'], '[]')
        self.assertEqual(result['data_object_stores'], '[]')

    def test_pack(self):
        context = testing.DummyResource()
        request = testing.DummyRequest()
        inst = self._makeOne(context, request)
        conn = DummyConnection(am=None)
        inst.get_connection = lambda *arg: conn
        request.POST['days'] = '5'
        request.sdiapi = DummySDIAPI()
        resp = inst.pack()
        self.assertEqual(conn._db.packed, 5)
        self.assertEqual(resp.location, '/mgmt_path')

    def test_pack_invalid_days(self):
        from pyramid.httpexceptions import HTTPFound
        context = testing.DummyResource()
        request = testing.DummyRequest()
        inst = self._makeOne(context, request)
        conn = DummyConnection(am=None)
        inst.get_connection = lambda *arg: conn
        request.POST['days'] = 'p'
        request.sdiapi = DummySDIAPI()
        self.assertRaises(HTTPFound, inst.pack)

    def test_flush_cache(self):
        context = testing.DummyResource()
        request = testing.DummyRequest()
        inst = self._makeOne(context, request)
        conn = DummyConnection(am=None)
        inst.get_connection = lambda *arg: conn
        request.POST['days'] = '5'
        request.sdiapi = DummySDIAPI()
        resp = inst.flush_cache()
        self.assertTrue(conn._db.minimized)
        self.assertEqual(resp.location, '/mgmt_path')

class DummyDB(object):
    def __init__(self, am=None):
        self.am = am

    def getActivityMonitor(self):
        return self.am

    def pack(self, days=None):
        self.packed = days

    def cacheMinimize(self):
        self.minimized = True

class DummyActivityMonitor(object):
    def getActivityAnalysis(self):
        return [{'end':1, 'connections':1, 'stores':1, 'loads':1}]*2

class DummyConnection(object):
    def __init__(self, am=None):
        self._db = DummyDB(am=am)

    def db(self):
        return self._db

class DummySDIAPI(object):
    def mgmt_path(self, *arg, **kw):
        return '/mgmt_path'
