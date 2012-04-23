import os
import tempfile
import shutil
import unittest
from pyramid import testing
from pyramid.exceptions import ConfigurationError

class TestFormView(unittest.TestCase):
    def _getTargetClass(self):
        from . import FormView
        return FormView
        
    def _makeOne(self, request):
        klass = self._getTargetClass()
        inst = klass(request)
        return inst

    def test___call__show(self):
        schema = DummySchema()
        request = testing.DummyRequest()
        inst = self._makeOne(request)
        inst.schema = schema
        inst.form_class = DummyForm
        result = inst()
        self.assertEqual(result,
                         {'css_links': (), 'js_links': (), 'form': 'rendered'})

    def test___call__show_result_response(self):
        from webob import Response
        schema = DummySchema()
        request = testing.DummyRequest()
        inst = self._makeOne(request)
        inst.schema = schema
        inst.form_class = DummyForm
        response = Response()
        inst.show = lambda *arg: response
        result = inst()
        self.assertEqual(result, response)

    def test___call__button_in_request(self):
        schema = DummySchema()
        request = testing.DummyRequest()
        request.POST['submit'] = True
        inst = self._makeOne(request)
        inst.schema = schema
        inst.buttons = (DummyButton('submit'), )
        inst.submit_success = lambda *x: 'success'
        inst.form_class = DummyForm
        result = inst()
        self.assertEqual(result, 'success')
        
    def test___call__button_in_request_fail(self):
        schema = DummySchema()
        request = testing.DummyRequest()
        request.POST['submit'] = True
        inst = self._makeOne(request)
        inst.schema = schema
        inst.buttons = (DummyButton('submit'), )
        import deform.exception
        def raiseit(*arg):
            raise deform.exception.ValidationFailure(None, None, None)
        inst.submit_success = raiseit
        inst.form_class = DummyForm
        inst.submit_failure = lambda *arg: 'failure'
        result = inst()
        self.assertEqual(result, 'failure')

    def test___call__button_in_request_fail_no_failure_handler(self):
        schema = DummySchema()
        request = testing.DummyRequest()
        request.POST['submit'] = True
        inst = self._makeOne(request)
        inst.schema = schema
        inst.buttons = (DummyButton('submit'), )
        import deform.exception
        def raiseit(*arg):
            exc = deform.exception.ValidationFailure(None, None, None)
            exc.render = lambda *arg: 'failure'
            raise exc
        inst.submit_success = raiseit
        inst.form_class = DummyForm
        result = inst()
        self.assertEqual(result,
                         {'css_links': (), 'js_links': (), 'form': 'failure'})


class TestFileUploadTempStore(unittest.TestCase):
    def setUp(self):
        self.tempdir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tempdir)
        
    def _getTargetClass(self):
        from . import FileUploadTempStore
        return FileUploadTempStore

    def _makeOne(self, request):
        return self._getTargetClass()(request)

    def _makeRequest(self):
        request = testing.DummyRequest()
        request.registry.settings = {}
        request.registry.settings['substanced.form.tempdir'] = self.tempdir
        request.session = DummySession()
        return request

    def test_no_tempdir_in_settings(self):
        request = testing.DummyRequest()
        request.registry.settings = {}
        self.assertRaises(ConfigurationError, self._makeOne, request)

    def test_preview_url(self):
        request = self._makeRequest()
        inst = self._makeOne(request)
        self.assertEqual(inst.preview_url(None), None)

    def test_contains_true(self):
        request = self._makeRequest()
        inst = self._makeOne(request)
        inst.tempstore['a'] = 1
        self.assertTrue('a' in inst)
        
    def test_contains_false(self):
        request = self._makeRequest()
        inst = self._makeOne(request)
        self.assertFalse('a' in inst)

    def test_setitem_stream_None(self):
        request = self._makeRequest()
        inst = self._makeOne(request)
        inst['a'] = {}
        self.assertEqual(inst.tempstore['a'], {})
        self.assertTrue(request.session._changed)

    def test_setitem_stream_file(self):
        request = self._makeRequest()
        inst = self._makeOne(request)
        here = os.path.dirname(__file__)
        thisfile = os.path.join(here, 'tests.py')
        inst['a'] = {'fp':open(thisfile, 'rb')}
        self.assertTrue(inst.tempstore['a']['randid'])
        fn = os.path.join(self.tempdir, inst.tempstore['a']['randid'])
        self.assertTrue(open(fn).read(),
                        open(thisfile, 'rb').read())
        self.assertTrue(request.session._changed)

    def test_get_data_None(self):
        request = self._makeRequest()
        inst = self._makeOne(request)
        self.assertEqual(inst.get('a', True), True)

    def test_get_no_randid(self):
        request = self._makeRequest()
        inst = self._makeOne(request)
        inst.tempstore['a'] = {'fp':True}
        self.assertEqual(inst.get('a'), {'fp':True})

    def test_get_with_randid(self):
        request = self._makeRequest()
        inst = self._makeOne(request)
        fn = os.path.join(self.tempdir, '1234')
        with open(fn, 'wb') as f:
            f.write('abc')
        inst.tempstore['a'] = {'randid':'1234'}
        self.assertEqual(inst.get('a')['fp'].read(),
                         open(fn, 'rb').read())

    def test___getitem___notfound(self):
        request = self._makeRequest()
        inst = self._makeOne(request)
        self.assertRaises(KeyError, inst.__getitem__, 'a')
        
    def test___getitem___found(self):
        request = self._makeRequest()
        inst = self._makeOne(request)
        inst.tempstore['a'] = {}
        self.assertEqual(inst['a'], {})

class DummyForm(object):
    def __init__(self, schema, buttons=None, use_ajax=False, ajax_options=''):
        self.schema = schema
        self.buttons = buttons
        self.use_ajax = use_ajax
        self.ajax_options = ajax_options

    def get_widget_resources(self):
        return {'js':(), 'css':()}

    def render(self, appstruct=None):
        self.appstruct = appstruct
        return 'rendered'

    def validate(self, controls):
        return {'_csrf_token_':'abc', 'validated':'validated'}

class DummySchema(object):
    name = 'schema'
    description = 'desc'
    title = 'title'
    
    def bind(self, **kw):
        self.kw = kw
        return self
    
class DummyButton(object):
    def __init__(self, name):
        self.name = name
        
class DummySession(dict):
    _changed = False
    def changed(self):
        self._changed = True

