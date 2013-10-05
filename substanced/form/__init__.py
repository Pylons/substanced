import binascii
import os
from pkg_resources import resource_filename

from translationstring import ChameleonTranslate

from pyramid.i18n import get_localizer
from pyramid.renderers import get_renderer
from pyramid.threadlocal import get_current_request

import deform
import deform.form
import deform.exception
from deform.template import ZPTTemplateLoader
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

class DeformRendererFactory(object):
    """
    Construct a custom Chameleon ZPT :term:`renderer` for Deform/Substance D.

    If the template name is an asset spec (ends with a concrete filename
    extension), use the Pyramid rendering machinery to resolve it.
    Otherwise, fall back to the Deform rendering (search-path-based)
    machinery to resolve it.

    This allows users to specify templates without the trouble of needing to
    add search paths to the deform rendering machinery.

    **Arguments**

    search_path
      A sequence of strings representing fully qualified filesystem
      directories containing Deform Chameleon template sources.  The
      order in which the directories are listed within ``search_path``
      is the order in which they are checked for the template provided
      to the renderer.

    auto_reload
       If true, automatically reload templates when they change (slows
       rendering).  Default: ``True``.

    debug
       If true, show nicer tracebacks during Chameleon template rendering
       errors (slows rendering).  Default: ``True``.

    encoding
       The encoding that the on-disk representation of the templates
       and all non-ASCII values passed to the template should be
       expected to adhere to.  Default: ``utf-8``.

    translator
       A translation function used for internationalization when the
       ``i18n:translate`` attribute syntax is used in the Chameleon
       template is active or a
       :class:`translationstring.TranslationString` is encountered
       during output.  It must accept a translation string and return
       an interpolated translation.  Default: ``None`` (no translation
       performed).
    """
    def __init__(self, search_path, auto_reload=True, debug=False,
                 encoding='utf-8', translator=None):
        self.translate = translator
        loader = ZPTTemplateLoader(search_path=search_path,
                                   auto_reload=auto_reload,
                                   debug=debug,
                                   encoding=encoding,
                                   translate=ChameleonTranslate(translator))
        self.loader = loader

    def __call__(self, template_name, **kw):
        return self.load(template_name)(**kw)

    def load(self, template_name):
        name, ext = os.path.splitext(template_name)
        if ext:
            return get_renderer(template_name).implementation()
        else:
            return self.loader.load(template_name + '.pt')

def translator(term): # pragma: no cover
    return get_localizer(get_current_request()).translate(term)

def includeme(config): # pragma: no cover
    deform_dir = resource_filename('deform', 'templates/')
    search_path = (deform_dir,)
    default_renderer = DeformRendererFactory(search_path, translator=translator)
    deform.Form.set_default_renderer(default_renderer)
