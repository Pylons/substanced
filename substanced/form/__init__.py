import deform
import deform.form
import deform.exception
import deform.widget

class FormView(object):
    form_class = deform.form.Form
    buttons = ()
    schema = None

    def __init__(self, request):
        self.request = request

    def __call__(self):
        use_ajax = getattr(self, 'use_ajax', False)
        ajax_options = getattr(self, 'ajax_options', '{}')
        self.schema = self.schema.bind(request=self.request)
        form = self.form_class(self.schema, buttons=self.buttons,
                               use_ajax=use_ajax, ajax_options=ajax_options)
        self.before(form)
        reqts = form.get_widget_resources()
        result = None

        for button in form.buttons:
            if button.name in self.request.POST:
                success_method = getattr(self, '%s_success' % button.name)
                try:
                    controls = self.request.POST.items()
                    validated = form.validate(controls)
                    result = success_method(validated)
                except deform.exception.ValidationFailure, e:
                    fail = getattr(self, '%s_failure' % button.name, None)
                    if fail is None:
                        fail = self.failure
                    result = fail(e)
                break

        if result is None:
            result = self.show(form)

        if isinstance(result, dict):
            result['js_links'] = reqts['js']
            result['css_links'] = reqts['css']

        return result

    def before(self, form):
        pass

    def failure(self, e):
        return {
            'form':e.render(),
            }

    def show(self, form):
        return {
            'form':form.render(),
            }

