import binascii
import os

import deform
import deform.form
import deform.exception
import deform.widget

from pyramid.exceptions import ConfigurationError

from ..util import chunks

# assume jquery is already loaded in our widget resource list, use asset
# specs instead of relative paths

default_resources = {
    'jquery': {
        None:{
            'js':'deform:static/scripts/jquery-2.0.3.min.js',
            },
        },
    'jquery.form': {
        None:{
            'js':('deform:static/scripts/jquery-2.0.3.min.js',
                  'deform:static/scripts/jquery.form-3.09.js'),
            },
        },
    'jquery.maskedinput': {
        None:{
            'js':('deform:static/scripts/jquery-2.0.3.min.js',
                  'deform:static/scripts/jquery.maskedinput-1.3.1.min.js'),
            },
        },
    'jquery.maskMoney': {
        None:{
            'js':('deform:static/scripts/jquery-2.0.3.min.js',
                  'deform:static/scripts/jquery.maskMoney-1.4.1.js'),
            },
        },
    'deform': {
        None:{
            'js':('deform:static/scripts/jquery-2.0.3.min.js',
                  'deform:static/scripts/jquery.form-3.09.js',
                  'deform:static/scripts/bootstrap.min.js',
                  'deform:static/scripts/deform.js'),
            'css':('deform:static/css/bootstrap.min.css',)
            },
        },
    'tinymce': {
        None:{
            'js':'deform:static/tinymce/tinymce.min.js',
            },
        },
    'typeahead': {
        None:{
            'js':'deform:static/scripts/typeahead.min.js',
            'css':'deform:static/css/typeahead.css'
            },
        },
    'modernizr': {
        None:{
            'js':('deform:static/scripts/modernizr.custom.input-types-and-atts.js',),
            },
        },
    'pickadate': {
        None: {
            'js': (
                'deform:static/scripts/pickadate.date.min.js',
                'deform:static/scripts/pickadate.min.js'
            ),
            'css': (
                'deform:static/css/pickadate-classic.date.min.css',
                'deform:static/css/pickadate-classic.min.css'
            )
        }
    }
    }

resource_registry = deform.widget.ResourceRegistry(use_defaults=False)
resource_registry.registry = default_resources

class FormError(Exception):
    """Non-validation-related error.
    """

class Form(deform.form.Form):
    """ Subclass of ``deform.form.Form`` which uses a custom resource
    registry designed for Substance D. XXX point at deform docs. """
    default_resource_registry = resource_registry

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
        self.schema = self.schema.bind(
            request=self.request, context=self.context)
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

