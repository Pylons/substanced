import mimetypes

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
from substanced.form import FormView

from .form import (
    SessionTempStore,
    chunks,
    )

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
                        raise colander.Invalid(node, e.message, value)
            else:
                try:
                    context.check_name(value)
                except Exception as e:
                    raise colander.Invalid(node, e.message, value)

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

@content(DocumentType, icon='icon-align-left', add_view='add_document', 
         name='Document')
class Document(Persistent):

    __propschema__ = DocumentSchema()

    def __init__(self, title, body):
        self.title = title
        self.body = body

    def texts(self): # for indexing
        return self.title, self.body
        
    def get_properties(self):
        return dict(name=self.__name__, body=self.body, title=self.title)

    def set_properties(self, struct):
        newname = struct['name']
        oldname = self.__name__
        if newname != oldname:
            parent = self.__parent__
            parent.rename(oldname, newname)
        self.body = struct['body']
        self.title = struct['title']

    
@mgmt_view(context=IFolder, name='add_document', tab_title='Add Document', 
           permission='sdi.add-content', 
           renderer='substanced.sdi:templates/form.pt', tab_condition=False)
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
    tmpstore = SessionTempStore(request)
    return deform.widget.FileUploadWidget(tmpstore)

class FileSchema(Schema):
    name = colander.SchemaNode(
        colander.String(),
        validator = make_name_validator(FileType),
        )
    stream = colander.SchemaNode(
        deform.schema.FileData(),
        widget = upload_widget,
        title = 'File',
        )
    mimetype = colander.SchemaNode(
        colander.String(),
        missing=colander.null,
        )

@content(FileType, name='File', icon='icon-file', add_view='add_file')
class File(Persistent):

    # prevent download tab from sorting first (it would show the file
    # when manage_main clicked)
    __tab_order__ = ('properties', 'acl_edit', 'download')

    __propschema__ = FileSchema()

    def __init__(self, stream, mimetype='application/octet-stream'):
        self.mimetype = mimetype
        self.blob = Blob()
        self.upload(stream)
           
    def get_properties(self):
        filedata = dict(
            fp=None,
            uid=str(self.__objectid__),
            filename=self.__name__,
            )
        return dict(name=self.__name__, file=filedata, mimetype=self.mimetype)

    def set_properties(self, struct):
        newname = struct['name']
        oldname = self.__name__
        if newname != oldname:
            parent = self.__parent__
            parent.rename(oldname, newname)
        if struct['fp']:
            self.upload(struct['fp'])
            self.mimetype = mimetypes.guess_type(
                struct['filename'], strict=False)[0]
        
    def upload(self, stream):
        fp = self.blob.open('w')
        size = 0
        for chunk in chunks(stream):
            size += len(chunk)        
            fp.write(chunk)
        fp.close()
        self.size = size

@mgmt_view(context=IFolder,
           name='add_file',
           tab_title='Add File', 
           permission='sdi.add-content', 
           renderer='substanced.sdi:templates/form.pt',
           tab_condition=False)
class AddFileView(FormView):
    title = 'Add Document'
    schema = FileSchema()
    buttons = ('add',)

    def add_success(self, appstruct):
        registry = self.request.registry
        name = appstruct.pop('name')
        filedata = appstruct.pop('stream')
        stream = filedata['fp']
        mimetype = appstruct['mimetype']
        if not mimetype:
            mimetype = mimetypes.guess_type(
                filedata['filename'], strict=False)[0]
        fileob = registry.content.create(FileType, stream, mimetype)
        self.request.context[name] = fileob
        return HTTPFound(self.request.mgmt_path(fileob, '@@properties'))

@mgmt_view(context=FileType,
           name='download',
           tab_title='Download',
           permission='sdi.view')
def download_tab(context, request):
    return HTTPFound(location=request.mgmt_path(context))
    
@mgmt_view(context=FileType,
           name='', 
           permission='sdi.view',
           tab_condition=False)
def download_file(context, request):
    return FileResponse(context.blob.committed(), request=request,
                        content_type=context.mimetype)
    
