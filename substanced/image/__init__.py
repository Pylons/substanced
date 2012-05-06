import colander

import deform.schema

from ..content import content
from ..form import FileUploadTempStore
from ..schema import Schema
from ..interfaces import IImage
from ..file import (
    FileUploadPropertySheet,
    FilePropertySheet,
    File,
    )

class ImageUploadTempStore(FileUploadTempStore):
    def preview_url(self, uid):
        root = self.request.root
        return self.request.mgmt_path(root, '@@preview_uploaded_image', uid)

@colander.deferred
def image_upload_widget(node, kw):
    request = kw['request']
    tmpstore = ImageUploadTempStore(request)
    widget = deform.widget.FileUploadWidget(tmpstore)
    widget.template = 'image_upload'
    return widget

imagenode = colander.SchemaNode(
    deform.schema.FileData(),
    widget = image_upload_widget,
    )

class ImageUploadSchema(Schema):
    file = imagenode.clone()

class ImageUploadPropertySheet(FileUploadPropertySheet):
    schema = ImageUploadSchema()
    
@content(
    IImage,
    name='Image',
    icon='icon-camera',
    add_view='add_image',
    # prevent view tab from sorting first (it would display the image when
    # manage_main clicked)
    tab_order = ('properties', 'acl_edit', 'view'),
    propertysheets = (
        ('Basic', FilePropertySheet),
        ('Upload', ImageUploadPropertySheet),
        ),
    catalog = True,
    )
class Image(File):
    pass

def includeme(config):
    config.scan('.')

