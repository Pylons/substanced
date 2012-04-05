import unittest
from pyramid import testing

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
        
