import os
import warnings
import colander
import StringIO
import mimetypes
from persistent import Persistent
from ZODB.blob import Blob
from zope.interface import implementer

from pyramid.response import FileResponse

try:
    import magic
except ImportError: # pragma: no cover
    magic = None

USE_MAGIC = object()

import deform.widget
import deform.schema

from ..content import content
from ..util import chunks
from ..form import FileUploadTempStore
from ..schema import Schema
from ..property import PropertySheet
from ..interfaces import IFile
from ..util import _make_name_validator

class FilePropertiesSchema(Schema):
    name = colander.SchemaNode(
        colander.String(),
        validator = _make_name_validator('File'),
        )
    title = colander.SchemaNode(
        colander.String(),
        missing='',
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
            title=context.title,
            )

    def set(self, struct):
        context = self.context
        newname = struct['name']
        mimetype = struct['mimetype']
        title = struct['title']
        context.mimetype = mimetype
        context.title = title
        oldname = context.__name__
        if newname and newname != oldname:
            context.__parent__.rename(oldname, newname)

@colander.deferred
def file_upload_widget(node, kw):
    request = kw['request']
    tmpstore = FileUploadTempStore(request)
    widget = deform.widget.FileUploadWidget(tmpstore)
    widget.template = 'substanced.file:templates/file_upload.pt'
    return widget

class FileNode(colander.SchemaNode):
    schema_type = deform.schema.FileData
    widget = file_upload_widget

class FileUploadSchema(Schema):
    file = FileNode()

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
        filename = file.get('filename', USE_MAGIC)
        fp = file.get('fp')
        if fp:
            fp.seek(0)
            context.upload(fp, mimetype_hint=filename)

    def after_set(self):
        PropertySheet.after_set(self)
        tmpstore = FileUploadTempStore(self.request)
        tmpstore.clear()

@content(
    'File',
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
@implementer(IFile)
class File(Persistent):

    title = u''

    def __init__(self, stream=None, mimetype=None, title=u''):
        """ The constructor of a File object.

        ``stream`` should be a filelike object (an object with a ``read``
        method that takes a size argument) or ``None``.  If stream is
        ``None``, the blob attached to this file object is created empty.

        ``title`` must be a string or Unicode object.

        ``mimetype`` may be any of the following:

        - ``None``, meaning set this file object's mimetype to
          ``application/octet-stream`` (the default).

        - A mimetype string (e.g. ``image/gif``)

        - The constant :attr:`substanced.file.USE_MAGIC`, which will
          derive the mimetype from the stream content (if ``stream`` is also
          supplied) using the ``python-magic`` library.

          .. warning::

             On non-Linux systems, successful use of
             :attr:`substanced.file.USE_MAGIC` requires the installation
             of additional dependencies.  See :ref:`optional_dependencies`.
        """
        self.blob = Blob()
        self.mimetype = mimetype or 'application/octet-stream'
        self.title = title or u''
        if stream is not None:
            if mimetype is USE_MAGIC:
                hint = USE_MAGIC
            else:
                hint = None
            self.upload(stream, mimetype_hint=hint)

    def upload(self, stream, mimetype_hint=None):
        """ Replace the current contents of this file's blob with the
        contents of ``stream``.  ``stream`` must be a filelike object (it
        must have a ``read`` method that takes a size argument).

        ``mimetype_hint`` can be any of the following:

        - ``None``, meaning don't reset the current mimetype.  This is the
          default.  If you already know the file's mimetype, and you don't
          want it divined from a filename or stream content, use ``None`` as
          the ``mimetype_hint`` value, and set the ``mimetype`` attribute of
          the file object directly before or after calling this method.

        - A string containing a filename that has an extension; the mimetype
          will be derived from the extension in the filename using the Python
          ``mimetypes`` module, and the result will be set as the mimetype
          attribute of this object.

        - The constant :attr:`pyramid.file.USE_MAGIC`, which will derive
          the mimetype using the ``python-magic`` library based on the
          stream's actual content.  The result will be set as the mimetype
          attribute of this object.

          .. warning::

             On non-Linux systems, successful use of
             :attr:`substanced.file.USE_MAGIC` requires the installation
             of additional dependencies.  See :ref:`optional_dependencies`.
          
        """
        if not stream:
            stream = StringIO.StringIO()
        fp = self.blob.open('w')
        first = True
        use_magic = False
        if mimetype_hint is USE_MAGIC:
            use_magic = True
            if magic is None: # pragma: no cover
                warnings.warn(
                    'The python-magic library does not have its requisite '
                    'dependencies installed properly, therefore the '
                    '"USE_MAGIC" flag passed to this method has been ignored '
                    '(it has been converted to "None").  The mimetype of '
                    'substanced.file.File objects created may be incorrect as '
                    'a result.'
                    )
                use_magic = False
                mimetype_hint = None

        if not use_magic:
            if mimetype_hint is not None:
                mimetype, _ = mimetypes.guess_type(mimetype_hint, strict=False)
                if mimetype is None:
                    mimetype = 'application/octet-stream'
                self.mimetype = mimetype
        for chunk in chunks(stream):
            if use_magic and first:
                first = False
                m = magic.Magic(mime=True)
                mimetype = m.from_buffer(chunk)
                self.mimetype = mimetype
            fp.write(chunk)
        fp.close()

    def get_response(self, **kw):
        """ Return a WebOb-compatible response object which uses the blob
        content as the stream data and the mimetype of the file as the
        content type.  The ``**kw`` arguments will be passed to the
        ``pyramid.response.FileResponse`` constructor as its keyword
        arguments."""
        if not 'content_type' in kw:
            kw['content_type'] = self.mimetype
        path = self.blob.committed()
        response = FileResponse(path, **kw)
        return response

    def get_size(self):
        """ Return the size in bytes of the data in the blob associated with
        the file"""
        return os.stat(self.blob.committed()).st_size

def includeme(config): # pragma: no cover
    config.scan('.')
