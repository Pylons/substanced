import os
import StringIO
import colander
import unittest
import pkg_resources
from pyramid import testing

class Test_view_file(unittest.TestCase):
    def _callFUT(self, context, request):
        from ..views import view_file
        return view_file(context, request)

    def test_it(self):
        context = testing.DummyResource()
        request = testing.DummyRequest()
        def get_response(**kw):
            self.assertEqual(kw['request'], request)
            return 'response'
        context.get_response = get_response
        result = self._callFUT(context, request)
        self.assertEqual(result, 'response')

class Test_view_tab(unittest.TestCase):
    def _callFUT(self, context, request):
        from ..views import view_tab
        return view_tab(context, request)

    def test_it(self):
        context = testing.DummyResource()
        request = testing.DummyRequest()
        request.mgmt_path = lambda *arg: '/mgmt'
        result = self._callFUT(context, request)
        self.assertEqual(result.location, '/mgmt')

class Test_name_or_file(unittest.TestCase):
    def setUp(self):
        testing.setUp()

    def tearDown(self):
        testing.tearDown()
        
    def _makeOne(self, node, kw):
        from ..views import name_or_file
        return name_or_file(node, kw)

    def test_no_file_no_name(self):
        inst = self._makeOne(None, None)
        self.assertRaises(
            colander.Invalid, inst, None, {'file':None, 'name':None}
            )

    def test_no_name_no_filename(self):
        inst = self._makeOne(None, None)
        self.assertRaises(
            colander.Invalid, inst, None, {'file':{'a':1}, 'name':None}
            )

    def test_no_name_with_filename(self):
        context = testing.DummyResource()
        context.check_name = lambda *arg: None
        request = testing.DummyRequest()
        request.registry.content = DummyContent(False)
        node = {'file':None}
        inst = self._makeOne(node, {'context':context, 'request':request})
        result = inst(node, {'file':{'filename':'another'}, 'name':None})
        self.assertEqual(result, None)

class TestAddFileView(unittest.TestCase):
    def setUp(self):
        testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _makeOne(self, context, request):
        from ..views import AddFileView
        return AddFileView(context, request)

    def test_add_success_no_filedata(self):
        created = testing.DummyResource()
        context = testing.DummyResource()
        request = testing.DummyRequest()
        request.mgmt_path = lambda *arg: '/mgmt'
        request.registry.content = DummyContent(created)
        appstruct = {'name':'abc', 'file':None}
        inst = self._makeOne(context, request)
        result = inst.add_success(appstruct)
        self.assertEqual(result.location, '/mgmt')
        self.assertEqual(context['abc'], created)

    def test_add_success_with_filedata_no_name(self):
        created = testing.DummyResource()
        context = testing.DummyResource()
        request = testing.DummyRequest()
        request.mgmt_path = lambda *arg: '/mgmt'
        request.registry.content = DummyContent(created)
        fp = StringIO.StringIO('abc')
        appstruct = {'name':None, 'file':{'fp':fp, 'filename':'filename'}}
        inst = self._makeOne(context, request)
        result = inst.add_success(appstruct)
        self.assertEqual(result.location, '/mgmt')
        self.assertEqual(context['filename'], created)

    def test_add_success_with_filedata_and_name(self):
        created = testing.DummyResource()
        context = testing.DummyResource()
        request = testing.DummyRequest()
        request.mgmt_path = lambda *arg: '/mgmt'
        request.registry.content = DummyContent(created)
        fp = StringIO.StringIO('abc')
        appstruct = {'name':'abc', 'file':{'fp':fp, 'filename':'filename'}}
        inst = self._makeOne(context, request)
        result = inst.add_success(appstruct)
        self.assertEqual(result.location, '/mgmt')
        self.assertEqual(context['abc'], created)

    def test_add_success_with_filedata_but_no_fp(self):
        created = testing.DummyResource()
        context = testing.DummyResource()
        request = testing.DummyRequest()
        request.mgmt_path = lambda *arg: '/mgmt'
        request.registry.content = DummyContent(created)
        appstruct = {'name':'abc', 'file':{'fp':None, 'filename':'filename'}}
        inst = self._makeOne(context, request)
        result = inst.add_success(appstruct)
        self.assertEqual(result.location, '/mgmt')
        self.assertEqual(context['abc'], created)

class Test_preview_image_upload(unittest.TestCase):
    def setUp(self):
        testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _callFUT(self, request):
        from ..views import preview_image_upload
        return preview_image_upload(request)

    def test_without_fp(self):
        here = os.path.dirname(__file__)
        request = testing.DummyRequest()
        request.subpath = ('abc',)
        request.registry.settings['substanced.uploads_tempdir'] = here
        response = self._callFUT(request)
        self.assertEqual(response.content_type, 'image/gif')
        fn = pkg_resources.resource_filename(
            'substanced.file', 'static/onepixel.gif')
        self.assertEqual(response.body, open(fn, 'rb').read())

    def test_with_fp(self):
        here = os.path.dirname(__file__)
        request = testing.DummyRequest()
        request.subpath = ('abc',)
        request.registry.settings['substanced.uploads_tempdir'] = here
        fp = StringIO.StringIO('abc')
        request.session['substanced.tempstore'] = {
            'abc':{'fp':fp, 'filename':'foo.jpg'}}
        response = self._callFUT(request)
        self.assertEqual(response.content_type, 'image/jpeg')
        self.assertEqual(response.body, 'abc')
        
class DummyContent(object):
    def __init__(self, result):
        self.result = result
    def istype(self, *arg, **kw):
        return self.result

    def create(self, *arg, **kw):
        return self.result
    
