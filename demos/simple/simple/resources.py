import mimetypes
import StringIO
import colander
import deform.widget

from persistent import Persistent
from ZODB.blob import Blob

from pyramid.httpexceptions import HTTPFound
from pyramid.response import FileResponse

from substanced.interfaces import (
    IFolder,
    IPropertied,
    ICatalogable,
    )
from substanced.schema import Schema
from substanced.content import content
from substanced.sdi import mgmt_view
from substanced.form import (
    FormView,
    FileUploadTempStore,
    )
from substanced.util import chunks

def make_name_validator(content_type):
    @colander.deferred
    def name_validator(node, kw):
        context = kw['request'].context
        def exists(node, value):
            if content_type.providedBy(context):
                if value != context.__name__:
                    try:
                        context.__parent__.check_name(value)
                    except Exception as e:
                        raise colander.Invalid(node, e.args[0], value)
            else:
                try:
                    context.check_name(value)
                except Exception as e:
                    raise colander.Invalid(node, e.args[0], value)

        return exists
    return name_validator

class DocumentType(IPropertied, ICatalogable):
    pass

class DocumentSchema(Schema):
    name = colander.SchemaNode(
        colander.String(),
        validator = make_name_validator(DocumentType),
        )
    title = colander.SchemaNode(
        colander.String(),
        )
    body = colander.SchemaNode(
        colander.String(),
        widget=deform.widget.RichTextWidget()
        )

class DocumentPropertySheet(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.schema = DocumentSchema().bind(request=request)
        
    def get(self):
        context = self.context
        return dict(name=self.__name__, body=context.body, title=context.title)

    def set(self, struct):
        context = self.context
        newname = struct['name']
        oldname = context.__name__
        if newname != oldname:
            parent = context.__parent__
            parent.rename(oldname, newname)
        context.body = struct['body']
        context.title = struct['title']

@content(
    DocumentType,
    icon='icon-align-left',
    add_view='add_document', 
    name='Document',
    )
class Document(Persistent):

    __propsheets__ = ( ('', DocumentSchema()), )

    def __init__(self, title, body):
        self.title = title
        self.body = body

    def texts(self): # for indexing
        return self.title, self.body
        
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
        document = registry.content.create(DocumentType, **appstruct)
        self.request.context[name] = document
        return HTTPFound(self.request.mgmt_path(document, '@@properties'))

class FileType(IPropertied, ICatalogable):
    pass
    
@colander.deferred
def upload_widget(node, kw):
    request = kw['request']
    tmpstore = FileUploadTempStore(request)
    return deform.widget.FileUploadWidget(tmpstore)

class FileSchema(Schema):
    file = colander.SchemaNode(
        deform.schema.FileData(),
        widget = upload_widget,
        missing = colander.null,
        )
    name = colander.SchemaNode(
        colander.String(),
        validator = make_name_validator(FileType),
        missing = colander.null,
        )
    mimetype = colander.SchemaNode(
        colander.String(),
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
                curried_name_validator = make_name_validator(FileType)
                real_name_validator = curried_name_validator(node, kw)
                real_name_validator(node['file'], filename)
    return _name_or_file

class FilePropertySheet(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.schema = FileSchema(validator=name_or_file).bind(request=request)

    def get(self):
        context = self.context
        filedata = dict(
            fp=None,
            uid=str(context.__objectid__),
            filename=context.__name__,
            )
        return dict(
            name=context.__name__,
            file=filedata,
            mimetype=self.mimetype
            )

    def set(self, struct):
        context = self.context
        newname = struct['name']
        file = struct['file']
        mimetype = struct['mimetype']
        if file and file.get('fp'):
            fp = file['fp']
            fp.seek(0)
            context.upload(fp)
            filename = file['filename']
            mimetype = mimetypes.guess_type(filename, strict=False)[0]
            if not newname:
                newname = filename
        if not mimetype:
            mimetype = 'application/octet-stream'
        context.mimetype = mimetype
        oldname = context.__name__
        if newname and newname != oldname:
            context.__parent__.rename(oldname, newname)
        
@content(
    FileType,
    name='File',
    icon='icon-file',
    add_view='add_file',
    )
class File(Persistent):

    # prevent view tab from sorting first (it would display the file when
    # manage_main clicked)
    __tab_order__ = ('properties', 'acl_edit', 'view')
    __propsheets__ = ( ('', FilePropertySheet), )

    def __init__(self, stream, mimetype='application/octet-stream'):
        self.mimetype = mimetype
        self.blob = Blob()
        self.upload(stream)
           
    def upload(self, stream):
        if not stream:
            stream = StringIO.StringIO()
        fp = self.blob.open('w')
        size = 0
        for chunk in chunks(stream):
            size += len(chunk)        
            fp.write(chunk)
        fp.close()
        self.size = size

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
    schema = FileSchema(validator=name_or_file)
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
        if not mimetype:
            mimetype = mimetypes.guess_type(name, strict=False)[0]
            if mimetype is None:
                mimetype = 'application/octet-stream'
        fileob = registry.content.create(FileType, stream, mimetype)
        self.request.context[name] = fileob
        return HTTPFound(self.request.mgmt_path(fileob, '@@properties'))

@mgmt_view(
    context=FileType,
    name='view',
    tab_title='View',
    permission='sdi.view'
    )
def view_tab(context, request):
    return HTTPFound(location=request.mgmt_path(context))
    
@mgmt_view(
    context=FileType,
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
    
