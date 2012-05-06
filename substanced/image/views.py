import pkg_resources
import mimetypes

from pyramid.httpexceptions import HTTPFound

import colander
import deform.schema

from pyramid.response import Response

from ..sdi import mgmt_view
from ..interfaces import (
    IFolder,
    IImage,
    )
from ..form import FormView

from ..file import (
    FilePropertiesSchema,
    )

from ..file.views import name_or_file

from . import (
    ImageUploadTempStore,
    image_upload_widget,
    )

onepixel = pkg_resources.resource_filename(
    'substanced.image', 'static/onepixel.gif')

# this doesn't require a permission, because it's based on session data
# which the user would have to put there anyway
@mgmt_view(name='preview_uploaded_image', tab_condition=False)
def preview_uploaded_image(request):
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
class AddImageView(FormView):
    title = 'Add File'
    schema = AddImageSchema(validator=name_or_file).clone()
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
        fileob = self.request.registry.content.create(IImage, stream)
        self.context[name] = fileob
        return HTTPFound(self.request.mgmt_path(fileob, '@@properties'))
