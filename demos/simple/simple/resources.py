import StringIO
import colander
import deform.widget

from persistent import Persistent
from ZODB.blob import Blob

from substanced.interfaces import (
    IPropertied,
    ICatalogable,
    )
from substanced.schema import Schema
from substanced.content import content
from substanced.form import FileUploadTempStore
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
    __propsheets__ = (
        ('', DocumentPropertySheet),
        )

    def __init__(self, title, body):
        self.title = title
        self.body = body

    def texts(self): # for indexing
        return self.title, self.body
        
class FileType(IPropertied, ICatalogable):
    pass
    
@colander.deferred
def upload_widget(node, kw):
    request = kw['request']
    tmpstore = FileUploadTempStore(request)
    return deform.widget.FileUploadWidget(tmpstore)

class FilePropertiesSchema(Schema):
    name = colander.SchemaNode(
        colander.String(),
        validator = make_name_validator(FileType),
        missing = colander.null,
        )
    mimetype = colander.SchemaNode(
        colander.String(),
        missing = colander.null,
        )

class FileUploadSchema(Schema):
    file = colander.SchemaNode(
        deform.schema.FileData(),
        widget = upload_widget,
        missing = colander.null,
        )

class FilePropertySheet(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.schema = FilePropertiesSchema().bind(request=request)

    def get(self):
        context = self.context
        return dict(
            name=context.__name__,
            mimetype=context.mimetype
            )

    def set(self, struct):
        context = self.context
        newname = struct['name']
        mimetype = struct['mimetype']
        if not mimetype:
            mimetype = 'application/octet-stream'
        context.mimetype = mimetype
        oldname = context.__name__
        if newname and newname != oldname:
            context.__parent__.rename(oldname, newname)

class FileUploadPropertySheet(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request
        self.schema = FileUploadSchema().bind(request=request)

    def get(self):
        context = self.context
        filedata = dict(
            fp=None,
            uid=str(context.__objectid__),
            filename=context.__name__,
            )
        return dict(file=filedata)
    
    def set(self, struct):
        context = self.context
        file = struct['file']
        if file and file.get('fp'):
            fp = file['fp']
            fp.seek(0)
            context.upload(fp)
        
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
    __propsheets__ = (
        ('basics', FilePropertySheet),
        ('upload', FileUploadPropertySheet),
        )

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

