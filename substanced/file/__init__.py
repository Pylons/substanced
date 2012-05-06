import os
import colander
import StringIO
from persistent import Persistent
from ZODB.blob import Blob

import magic

from pyramid.response import FileResponse

import deform.widget
import deform.schema

from ..content import content
from ..util import chunks
from ..form import FileUploadTempStore
from ..schema import Schema
from ..property import PropertySheet
from ..interfaces import IFile
from ..util import _make_name_validator

@colander.deferred
def file_upload_widget(node, kw):
    request = kw['request']
    tmpstore = FileUploadTempStore(request)
    widget = deform.widget.FileUploadWidget(tmpstore)
    widget.template = 'substanced.file:templates/file_upload.pt'
    return widget

class FilePropertiesSchema(Schema):
    name = colander.SchemaNode(
        colander.String(),
        validator = _make_name_validator(IFile),
        )
    mimetype = colander.SchemaNode(
        colander.String(),
        )

class FilePropertySheet(PropertySheet):
    schema = FilePropertiesSchema()

    def get(self):
        context = self.context
        return dict(
            name=context.__name__,
            mimetype=context.mimetype,
            )

    def set(self, struct):
        context = self.context
        newname = struct['name']
        mimetype = struct['mimetype']
        context.mimetype = mimetype
        oldname = context.__name__
        if newname and newname != oldname:
            context.__parent__.rename(oldname, newname)

filenode = colander.SchemaNode(
    deform.schema.FileData(),
    widget = file_upload_widget,
    )

class FileUploadSchema(Schema):
    file = filenode.clone()
    temp = colander.SchemaNode(
        colander.String(),
        )

class FileUploadPropertySheet(PropertySheet):
    schema = FileUploadSchema()
    
    def get(self):
        context = self.context
        request = self.request
        uid = str(context.__objectid__)
        filedata = dict(
            fp=None,
            uid=uid,
            filename='',
            size = context.get_size(),
            )
        if context.mimetype.startswith('image/'):
            filedata['preview_url'] = request.mgmt_path(context)
        return dict(file=filedata)
    
    def set(self, struct):
        context = self.context
        file = struct['file']
        fp = file.get('fp')
        if fp:
            fp.seek(0)
            context.upload(fp, set_mimetype=True)

    def after_set(self):
        PropertySheet.after_set(self)
        tmpstore = FileUploadTempStore(self.request)
        tmpstore.clear()

@content(
    IFile,
    name = 'File',
    icon='icon-file',
    add_view='add_file',
    # prevent view tab from sorting first (it would display the image when
    # manage_main clicked)
    tab_order = ('properties', 'acl_edit', 'view'),
    propertysheets = (
        ('Basic', FilePropertySheet),
        ('Upload', FileUploadPropertySheet),
        ),
    catalog = True,
    )
class File(Persistent):

    def __init__(self, stream=None, mimetype=None):
        self.blob = Blob()
        self.mimetype = mimetype or 'application/octet-stream'
        if stream is not None:
            self.upload(stream, set_mimetype=mimetype is None)

    def upload(self, stream, set_mimetype=False):
        if not stream:
            stream = StringIO.StringIO()
        fp = self.blob.open('w')
        first = True
        for chunk in chunks(stream):
            if set_mimetype and first:
                first = False
                m = magic.Magic(mime=True)
                mimetype = m.from_buffer(chunk)
                self.mimetype = mimetype
            fp.write(chunk)
        fp.close()

    def get_response(self, **kw):
        if not 'content_type' in kw:
            kw['content_type'] = self.mimetype
        path = self.blob.committed()
        response = FileResponse(path, **kw)
        return response

    def get_size(self):
        return os.stat(self.blob.committed()).st_size

def includeme(config): # pragma: no cover
    config.scan('.')
