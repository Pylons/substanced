from pyramid.security import NO_PERMISSION_REQUIRED
from pyramid.httpexceptions import (
    HTTPFound,
    HTTPForbidden,
    )

from .. import (
    mgmt_view,
    sdi_mgmt_views,
    )

class ManagementViews(object):
    # these defined as staticmethods only for test overriding
    sdi_mgmt_views = staticmethod(sdi_mgmt_views)
    
    def __init__(self, context, request):
        self.context = context
        self.request = request

    @mgmt_view(
        tab_condition=False,
        permission=NO_PERMISSION_REQUIRED,
        )
    @mgmt_view(
        name='manage_main',
        tab_condition=False,
        permission=NO_PERMISSION_REQUIRED,
        )
    def manage_main(self):
        request = self.request
        view_data = self.sdi_mgmt_views(self.context, request)
        if not view_data:
            request.session['came_from'] = request.url
            raise HTTPForbidden(
                location=request.sdiapi.mgmt_path(
                    request.virtual_root, '@@login')
                )
        view_name = '@@%s' % (view_data[0]['view_name'],)
        return HTTPFound(
            location=request.sdiapi.mgmt_path(request.context, view_name)
            )
