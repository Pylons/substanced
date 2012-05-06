import os
import unittest
from pyramid import testing

class TestImageUploadTempStore(unittest.TestCase):
    def setUp(self):
        testing.setUp()

    def tearDown(self):
        testing.tearDown()

    def _makeOne(self, request):
        from .. import ImageUploadTempStore
        return ImageUploadTempStore(request)

    def test_preview_url(self):
        here = os.path.dirname(__file__)
        request = testing.DummyRequest()
        request.registry.settings['substanced.uploads_tempdir'] = here
        request.mgmt_path = lambda *arg: '/mgmt'
        request.root = testing.DummyResource()
        inst = self._makeOne(request)
        self.assertEqual(inst.preview_url('uid'), '/mgmt')

class Test_image_upload_widget(unittest.TestCase):
    def setUp(self):
        testing.setUp()

    def tearDown(self):
        testing.tearDown()
        
    def _callFUT(self, node, kw):
        from .. import image_upload_widget
        return image_upload_widget(node, kw)
    
    def test_it(self):
        here = os.path.dirname(__file__)
        request = testing.DummyRequest()
        request.registry.settings['substanced.uploads_tempdir'] = here
        kw = {}
        kw['request'] = request
        widget = self._callFUT(None, kw)
        self.assertEqual(widget.__class__.__name__, 'FileUploadWidget')
        self.assertEqual(widget.template, 'image_upload')
        
