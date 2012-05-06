import os
import unittest
from pyramid import testing
from pkg_resources import resource_filename
import StringIO

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
        fn = resource_filename('substanced.image', 'static/onepixel.gif')
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

class TestAddImageView(unittest.TestCase):
    def setUp(self):
        testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _makeOne(self, context, request):
        from ..views import AddImageView
        return AddImageView(context, request)

    def test__makeob(self):
        from ...interfaces import IImage
        request = testing.DummyRequest()
        registry = testing.DummyResource()
        content = testing.DummyResource()
        request.registry = registry
        request.registry.content = content
        context = testing.DummyResource()
        def create(type, _stream):
            self.assertEqual(type, IImage)
            self.assertEqual(_stream, 'stream')
            return 'abc'
        content.create = create
        inst = self._makeOne(context, request)
        self.assertEqual(inst._makeob('stream'), 'abc')
        

