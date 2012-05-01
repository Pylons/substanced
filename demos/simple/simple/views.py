import mimetypes
import colander
import deform.schema

from pyramid.httpexceptions import HTTPFound
from pyramid.response import FileResponse
from pyramid.view import view_config

from substanced.sdi import mgmt_view
from substanced.form import FormView
from substanced.interfaces import IFolder

from .resources import (
    File,
    FilePropertiesSchema,
    DocumentSchema,
    upload_widget,
    make_name_validator,
    )

@view_config(renderer='templates/splash.pt')
def splash_view(request):
    manage_prefix = request.registry.settings.get('substanced.manage_prefix', 
                                                  '/manage')
    return {'manage_prefix': manage_prefix}

@colander.deferred
def name_or_file(node, kw):
    def _name_or_file(node, struct):
        if not struct['file'] and not struct['name']:
            raise colander.Invalid('One of name or file is required')
        if not struct['name']:
            if struct['file'] and struct['file'].get('filename'):
                filename = struct['file']['filename']
                curried_name_validator = make_name_validator('File')
                real_name_validator = curried_name_validator(node, kw)
                real_name_validator(node['file'], filename)
    return _name_or_file

class AddFileSchema(FilePropertiesSchema):
    file = colander.SchemaNode(
        deform.schema.FileData(),
        widget = upload_widget,
        missing = colander.null,
        )

@mgmt_view(
    context=IFolder,
    name='add_file',
    tab_title='Add File', 
    permission='sdi.add-content', 
    renderer='substanced.sdi:templates/form.pt',
    tab_condition=False
    )
class AddFileView(FormView):
    title = 'Add File'
    schema = AddFileSchema(validator=name_or_file).clone()
    schema['name'].missing = colander.null
    buttons = ('add',)

    def add_success(self, appstruct):
        registry = self.request.registry
        name = appstruct.pop('name')
        filedata = appstruct.pop('file')
        stream = None
        filename = None
        if filedata:
            filename = filedata['filename']
            stream = filedata['fp']
            if stream:
                stream.seek(0)
            else:
                stream = None
        mimetype = appstruct['mimetype']
        name = filename or name
        if not mimetype or mimetype == 'application/octet-stream':
            mimetype = mimetypes.guess_type(name, strict=False)[0]
            if mimetype is None:
                mimetype = 'application/octet-stream'
        fileob = registry.content.create('File', stream, mimetype)
        self.context[name] = fileob
        return HTTPFound(self.request.mgmt_path(fileob, '@@properties'))

@mgmt_view(
    context=File,
    name='view',
    tab_title='View',
    permission='sdi.view'
    )
def view_tab(context, request):
    return HTTPFound(location=request.mgmt_path(context))
    
@mgmt_view(
    context=File,
    name='', 
    permission='sdi.view',
    tab_condition=False
    )
def view_file(context, request):
    return FileResponse(
        context.blob.committed(),
        request=request,
        content_type=str(context.mimetype),
        )
    
@mgmt_view(
    context=IFolder,
    name='add_document',
    tab_title='Add Document', 
    permission='sdi.add-content', 
    renderer='substanced.sdi:templates/form.pt',
    tab_condition=False,
    )
class AddDocumentView(FormView):
    title = 'Add Document'
    schema = DocumentSchema()
    buttons = ('add',)

    def add_success(self, appstruct):
        registry = self.request.registry
        name = appstruct.pop('name')
        document = registry.content.create('Document', **appstruct)
        self.context[name] = document
        return HTTPFound(self.request.mgmt_path(document, '@@properties'))

