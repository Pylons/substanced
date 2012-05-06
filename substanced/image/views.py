import pkg_resources
import mimetypes

import colander
import deform.schema

from pyramid.response import Response

from ..sdi import mgmt_view
from ..interfaces import (
    IFolder,
    IImage,
    )

from ..file import (
    FilePropertiesSchema,
    )

from ..file.views import (
    name_or_file,
    AddFileView,
    )

from . import (
    ImageUploadTempStore,
    image_upload_widget,
    )

onepixel = pkg_resources.resource_filename(
    'substanced.image', 'static/onepixel.gif')

# this doesn't require a permission, because it's based on session data
# which the user would have to put there anyway
@mgmt_view(name='preview_image_upload', tab_condition=False)
def preview_image_upload(request):
    uid = request.subpath[0]
    tempstore = ImageUploadTempStore(request)
    filedata = tempstore.get(uid, {})
    fp = filedata.get('fp')
    if fp is None:
        filename = onepixel
        fp = open(onepixel, 'rb')
    else:
        fp.seek(0)
        filename = filedata['filename']
    mimetype = mimetypes.guess_type(filename, strict=False)[0]
    response = Response(content_type=mimetype, app_iter=fp)
    return response

class AddImageSchema(FilePropertiesSchema):
    file = colander.SchemaNode(
        deform.schema.FileData(),
        widget = image_upload_widget,
        missing = colander.null,
        )

@mgmt_view(
    context=IFolder,
    name='add_image',
    tab_title='Add Image', 
    permission='sdi.add-content', 
    renderer='substanced.sdi:templates/form.pt',
    tab_condition=False
    )
class AddImageView(AddFileView):
    title = 'Add Image'
    schema = AddImageSchema(validator=name_or_file).clone()
    schema['name'].missing = colander.null
    schema['mimetype'].missing = colander.null
    buttons = ('add',)

    def _makeob(self, stream):
        return self.request.registry.content.create(IImage, stream)

