import colander
import deform.schema

from pyramid.httpexceptions import HTTPFound

from substanced.sdi import mgmt_view
from substanced.form import FormView

from ..util import _make_name_validator

from . import (
    FilePropertiesSchema,
    file_upload_widget,
    )

from ..interfaces import (
    IFile,
    IFolder,
    )

@mgmt_view(
    context=IFile,
    name='', 
    permission='sdi.view',
    tab_condition=False
    )
def view_file(context, request):
    return context.get_response(request=request)

@mgmt_view(
    context=IFile,
    name='view',
    tab_title='View',
    permission='sdi.view'
    )
def view_tab(context, request):
    return HTTPFound(location=request.mgmt_path(context))

class AddFileSchema(FilePropertiesSchema):
    file = colander.SchemaNode(
        deform.schema.FileData(),
        widget = file_upload_widget,
        missing = colander.null,
        )

@colander.deferred
def name_or_file(node, kw):
    def _name_or_file(node, struct):
        if not struct['file'] and not struct['name']:
            raise colander.Invalid('One of name or file is required')
        if not struct['name']:
            if struct['file'] and struct['file'].get('filename'):
                filename = struct['file']['filename']
                curried_name_validator = _make_name_validator(IFile)
                real_name_validator = curried_name_validator(node, kw)
                real_name_validator(node['file'], filename)
    return _name_or_file

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
    schema['mimetype'].missing = colander.null
    buttons = ('add',)

    def add_success(self, appstruct):
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
        name = name or filename
        fileob = self.request.registry.content.create(IFile, stream)
        self.context[name] = fileob
        return HTTPFound(self.request.mgmt_path(fileob, '@@properties'))
