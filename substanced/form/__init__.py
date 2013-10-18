import binascii
import os
from pkg_resources import resource_filename

from pyramid.i18n import get_localizer
from pyramid.threadlocal import get_current_request

import deform
import deform.form
import deform.exception
from deform.template import ZPTRendererFactory
import deform.widget

from pyramid.exceptions import ConfigurationError

from ..util import chunks

class FormError(Exception):
    """Non-validation-related error.
    """

class Form(deform.form.Form):
    """ Subclass of ``deform.form.Form`` which uses a custom resource
    registry designed for Substance D. XXX point at deform docs. """

class FormView(object):
    """ A class which can be used as a view which introspects a schema to
    present the form.  XXX describe better using ``pyramid_deform``
    documentation."""
    form_class = Form
    buttons = ()
    schema = None

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def _build_form(self):
        use_ajax = getattr(self, 'use_ajax', False)
        ajax_options = getattr(self, 'ajax_options', '{}')
        action = getattr(self, 'action', '')
        method = getattr(self, 'method', 'POST')
        formid = getattr(self, 'formid', 'deform')
        autocomplete = getattr(self, 'autocomplete', None)
        request = self.request
        self.schema = self.schema.bind(
            request=request,
            context=self.context,
            # see substanced.schema.CSRFToken
            _csrf_token_=request.session.get_csrf_token(), 
            )
        form = self.form_class(self.schema, action=action, method=method,
                               buttons=self.buttons, formid=formid,
                               use_ajax=use_ajax, ajax_options=ajax_options,
                               autocomplete=autocomplete)
        # XXX override autocomplete; should be part of deform
        #form.widget.template = 'substanced:widget/templates/form.pt' 
        self.before(form)
        reqts = form.get_widget_resources()
        return form, reqts

    def __call__(self):
        form, reqts = self._build_form()
        result = None

        for button in form.buttons:
            if button.name in self.request.POST:
                success_method = getattr(self, '%s_success' % button.name)
                try:
                    controls = self.request.POST.items()
                    validated = form.validate(controls)
                except deform.exception.ValidationFailure as e:
                    fail = getattr(self, '%s_failure' % button.name, None)
                    if fail is None:
                        fail = self.failure
                    result = fail(e)
                else:
                    try:
                        result = success_method(validated)
                    except FormError as e:
                        snippet = '<div class="error">Failed: %s</div>' % e
                        self.request.sdiapi.flash(snippet, 'danger',
                                                  allow_duplicate=True)
                        result = {'form': form.render(validated)}
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

_marker = object()

class FileUploadTempStore(object):
    """ A Deform ``FileUploadTempStore`` implementation that stores file
    upload data in the Pyramid session and on disk.  The request passed to
    its constructor must be a fully-initialized Pyramid request (it have a
    ``registry`` attribute, which must have a ``settings`` attribute, which
    must be a dictionary).  The ``substanced.uploads_tempdir`` variable in the
    ``settings`` dictionary must be set to the path of an existing directory
    on disk.  This directory will temporarily store file upload data on
    behalf of Deform and Substance D when a form containing a file upload
    widget fails validation.

    See the :term:`Deform` documentation for more information about
    ``FileUploadTempStore`` objects.
    """
    def __init__(self, request):
        try:
            self.tempdir=request.registry.settings['substanced.uploads_tempdir']
        except KeyError:
            raise ConfigurationError(
                'To use FileUploadTempStore, you must set a  '
                '"substanced.uploads_tempdir" key in your .ini settings. It '
                'points to a directory which will temporarily '
                'hold uploaded files when form validation fails.')
        self.request = request
        self.session = request.session
        
    def preview_url(self, uid):
        root = self.request.virtual_root
        return self.request.sdiapi.mgmt_path(
            root, '@@preview_image_upload', uid)

    def __contains__(self, name):
        return name in self.session.get('substanced.tempstore', {})

    def __setitem__(self, name, data):
        newdata = data.copy()
        stream = newdata.pop('fp', None)

        if stream is not None:
            while True:
                randid = binascii.hexlify(os.urandom(20)).decode('ascii')
                fn = os.path.join(self.tempdir, randid)
                if not os.path.exists(fn): # XXX race condition
                    break
            newdata['randid'] = randid
            with open(fn, 'w+b') as fp:
                for chunk in chunks(stream):
                    fp.write(chunk)

        self._tempstore_set(name, newdata)

    def _tempstore_set(self, name, data):
        # cope with sessioning implementations that cant deal with
        # in-place mutation of mutable values (temporarily?)
        existing = self.session.get('substanced.tempstore', {})
        existing[name] = data
        self.session['substanced.tempstore'] = existing

    def clear(self):
        data = self.session.pop('substanced.tempstore', {})
        for k, v in data.items():
            if 'randid' in v:
                randid = v['randid']
                fn = os.path.join(self.tempdir, randid)
                try:
                    os.remove(fn)
                except OSError:
                    pass

    def get(self, name, default=None):
        data = self.session.get('substanced.tempstore', {}).get(name)

        if data is None:
            return default

        newdata = data.copy()
            
        randid = newdata.get('randid')

        if randid is not None:

            fn = os.path.join(self.tempdir, randid)
            try:
                newdata['fp'] = open(fn, 'rb')
            except IOError:
                pass

        return newdata

    def __getitem__(self, name):
        data = self.get(name, _marker)
        if data is _marker:
            raise KeyError(name)
        return data

def translator(term): # pragma: no cover
    return get_localizer(get_current_request()).translate(term)

def get_deform_renderer(search_paths):
    return ZPTRendererFactory(search_paths, translator=translator)

def includeme(config): # pragma: no cover
    deform_dir = resource_filename('deform', 'templates/')
    deform_renderer = get_deform_renderer((deform_dir,))
    deform.Form.set_default_renderer(deform_renderer)
