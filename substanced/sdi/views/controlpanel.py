from .. import (
    mgmt_view,
    sdi_mgmt_views,
    )

@mgmt_view(
    physical_path='/',
    tab_title='Control Panel',
    permission='sdi.view-controlpanel',
    renderer='templates/controlpanel.pt',
    name='controlpanel',
    )
def controlpanel(context, request):
    views = sdi_mgmt_views(context, request, category='controlpanel')
    return {'views':views}

