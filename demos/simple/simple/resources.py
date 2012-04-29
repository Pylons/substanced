import StringIO
import colander
import deform.widget

from persistent import Persistent
from ZODB.blob import Blob

from substanced.schema import Schema
from substanced.content import content
from substanced.form import FileUploadTempStore
from substanced.util import chunks
from substanced.property import PropertySheet

def make_name_validator(content_type):
    @colander.deferred
    def name_validator(node, kw):
        request = kw['request']
        context = request.context
        def exists(node, value):
            if request.registry.content.istype(context, content_type):
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

class DocumentSchema(Schema):
    name = colander.SchemaNode(
        colander.String(),
        validator = make_name_validator('Document'),
        )
    title = colander.SchemaNode(
        colander.String(),
        )
    body = colander.SchemaNode(
        colander.String(),
        widget=deform.widget.RichTextWidget()
        )

class DocumentPropertySheet(PropertySheet):
    schema = DocumentSchema()
    
    def __init__(self, context, request):
        self.context = context
        self.request = request

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
    'Document',
    icon='icon-align-left',
    add_view='add_document', 
    name='Document',
    propertysheets = (
        ('Basic', DocumentPropertySheet),
        ),
    catalog=True,
    )
class Document(Persistent):
    def __init__(self, title, body):
        self.title = title
        self.body = body

    def texts(self): # for indexing
        return self.title, self.body
        
@colander.deferred
def upload_widget(node, kw):
    request = kw['request']
    tmpstore = FileUploadTempStore(request)
    return deform.widget.FileUploadWidget(tmpstore)

class FilePropertiesSchema(Schema):
    name = colander.SchemaNode(
        colander.String(),
        validator = make_name_validator('File'),
        )
    mimetype = colander.SchemaNode(
        colander.String(),
        missing = 'application/octet-stream',
        )

class FilePropertySheet(PropertySheet):
    schema = FilePropertiesSchema()

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
        context.mimetype = mimetype
        oldname = context.__name__
        if newname and newname != oldname:
            context.__parent__.rename(oldname, newname)

class FileUploadSchema(Schema):
    file = colander.SchemaNode(
        deform.schema.FileData(),
        widget = upload_widget,
        )

class FileUploadPropertySheet(PropertySheet):
    schema = FileUploadSchema()
    
    def get(self):
        context = self.context
        filedata = dict(
            fp=None,
            uid=str(context.__objectid__),
            filename='',
            )
        return dict(file=filedata)
    
    def set(self, struct):
        context = self.context
        file = struct['file']
        if file.get('fp'):
            fp = file['fp']
            fp.seek(0)
            context.upload(fp)
        
@content(
    'File',
    icon='icon-file',
    add_view='add_file',
    # prevent view tab from sorting first (it would display the file when
    # manage_main clicked)
    tab_order = ('properties', 'acl_edit', 'view'),
    propertysheets = (
        ('Basic', FilePropertySheet),
        ('Upload', FileUploadPropertySheet),
        ),
    catalog = True,
    )
class File(Persistent):

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

