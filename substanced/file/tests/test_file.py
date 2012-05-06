import StringIO
import os
import unittest
from pyramid import testing

class Test_file_upload_widget(unittest.TestCase):
    def setUp(self):
        testing.setUp()

    def tearDown(self):
        testing.tearDown()
        
    def _callFUT(self, node, kw):
        from .. import file_upload_widget
        return file_upload_widget(node, kw)
    
    def test_it(self):
        here = os.path.dirname(__file__)
        request = testing.DummyRequest()
        request.registry.settings['substanced.uploads_tempdir'] = here
        kw = {}
        kw['request'] = request
        widget = self._callFUT(None, kw)
        self.assertEqual(widget.__class__.__name__, 'FileUploadWidget')
        
class TestFilePropertySheet(unittest.TestCase):
    def _makeOne(self, context, request):
        from .. import FilePropertySheet
        return FilePropertySheet(context, request)
    
    def test_get(self):
        context = testing.DummyResource()
        context.__name__ = 'name'
        context.mimetype = 'mimetype'
        request = testing.DummyRequest()
        inst = self._makeOne(context, request)
        self.assertEqual(inst.get(), {'name':'name', 'mimetype':'mimetype'})
        
    def test_set_no_name_change(self):
        context = testing.DummyResource()
        context.__name__ = 'name'
        context.mimetype = 'mimetype'
        request = testing.DummyRequest()
        inst = self._makeOne(context, request)
        inst.set({'mimetype':'newmimetype', 'name':'name'})
        self.assertEqual(inst.context.mimetype, 'newmimetype')

    def test_set_with_name_change(self):
        parent = testing.DummyResource()
        def rename(oldname, newname):
            self.assertEqual(oldname, 'name')
            self.assertEqual(newname, 'newname')
            context.renamed = True
        parent.rename = rename
        context = testing.DummyResource()
        context.__parent__ = parent
        context.__name__ = 'name'
        context.mimetype = 'mimetype'
        request = testing.DummyRequest()
        inst = self._makeOne(context, request)
        inst.set({'mimetype':'newmimetype', 'name':'newname'})
        self.assertEqual(inst.context.mimetype, 'newmimetype')
        self.assertTrue(context.renamed)

class TestFileUploadPropertySheet(unittest.TestCase):
    def setUp(self):
        testing.setUp()

    def tearDown(self):
        testing.tearDown()
        
    def _makeOne(self, context, request):
        from .. import FileUploadPropertySheet
        return FileUploadPropertySheet(context, request)
    
    def test_get(self):
        context = testing.DummyResource()
        context.__objectid__ = 'oid'
        request = testing.DummyRequest()
        request.mgmt_path = lambda *arg: '/manage'
        inst = self._makeOne(context, request)
        file = {'fp':None, 'uid':'oid', 'filename':'','preview_url':'/manage'}
        self.assertEqual(
            inst.get(),
            {'file':file}
            )
        
    def test_set_no_fp(self):
        context = testing.DummyResource()
        request = testing.DummyRequest()
        inst = self._makeOne(context, request)
        inst.set({'file':{}})

    def test_set_with_name_change(self):
        fp = StringIO.StringIO('abc')
        fp.seek(2)
        def upload(_fp, set_mimetype=False):
            self.assertEqual(_fp, fp)
            self.assertTrue(set_mimetype)
            context.uploaded = True
        context = testing.DummyResource()
        context.upload = upload
        request = testing.DummyRequest()
        inst = self._makeOne(context, request)
        inst.set({'file':{'fp':fp}})
        self.assertTrue(context.uploaded)
        self.assertEqual(fp.tell(), 0)

    def test_after_set(self):
        context = testing.DummyResource()
        here = os.path.dirname(__file__)
        request = testing.DummyRequest()
        request.registry.settings = {}
        request.registry.settings['substanced.uploads_tempdir'] = here
        request.session['substanced.tempstore'] = {'1':{}}
        request.flash_undo = lambda *arg: None
        inst = self._makeOne(context, request)
        inst.after_set()
        self.assertEqual(request.session.get('substanced.tempstore'), None)

class TestFile(unittest.TestCase):
    def setUp(self):
        testing.setUp()

    def tearDown(self):
        testing.tearDown()
        
    def _makeOne(self, stream, mimetype):
        from .. import File
        return File(stream, mimetype)

    def test_ctor_no_stream(self):
        inst = self._makeOne(None, None)
        self.assertEqual(inst.mimetype, 'application/octet-stream')
    
    def test_ctor_with_stream(self):
        stream = StringIO.StringIO('abc')
        inst = self._makeOne(stream, None)
        self.assertEqual(inst.mimetype, 'text/plain')
        fp = inst.blob.open('r')
        fp.seek(0)
        self.assertEqual(fp.read(), 'abc')
        
    def test_ctor_with_mimetype_no_stream(self):
        inst = self._makeOne(None, 'text/plain')
        self.assertEqual(inst.mimetype, 'text/plain')

    def test_ctor_with_mimetype_and_stream(self):
        stream = StringIO.StringIO('abc')
        inst = self._makeOne(stream, 'text/foo')
        self.assertEqual(inst.mimetype, 'text/foo')
        fp = inst.blob.open('r')
        fp.seek(0)
        self.assertEqual(fp.read(), 'abc')

    def test_upload_stream_is_None(self):
        inst = self._makeOne(None, None)
        inst.upload(None)
        self.assertEqual(inst.blob.open('r').read(), '')
        
    def test_upload_stream_is_not_None(self):
        stream = StringIO.StringIO('abc')
        inst = self._makeOne(None, None)
        inst.upload(stream)
        self.assertEqual(inst.blob.open('r').read(), 'abc')
        
    def test_upload_stream_set_mimetype_true(self):
        stream = StringIO.StringIO('abc')
        inst = self._makeOne(None, None)
        self.assertEqual(inst.mimetype, 'application/octet-stream')
        inst.upload(stream, set_mimetype=True)
        self.assertEqual(inst.mimetype, 'text/plain')

    def test_get_response_no_ct(self):
        inst = self._makeOne(None, 'text/plain')
        inst.blob = DummyBlob()
        response = inst.get_response()
        self.assertTrue(response.body)
        self.assertEqual(response.content_type, 'text/plain')

    def test_get_response_with_ct(self):
        inst = self._makeOne(None, 'text/plain')
        inst.blob = DummyBlob()
        response = inst.get_response(content_type='text/other')
        self.assertTrue(response.body)
        self.assertEqual(response.content_type, 'text/other')

    def test_get_suize(self):
        inst = self._makeOne(None, None)
        inst.blob = DummyBlob()
        size = inst.get_size()
        self.assertEqual(size, os.stat(__file__).st_size)
        
class DummyBlob(object):
    def committed(self):
        return os.path.abspath(__file__)
