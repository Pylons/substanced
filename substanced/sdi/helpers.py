import sys

from pyramid.renderers import get_renderer
from pyramid.location import lineage
from pyramid.security import has_permission

from pyramid.events import (
    subscriber,
    BeforeRender,
    )

from . import sdi_mgmt_views # API used by templates
sdi_mgmt_views = sdi_mgmt_views # pyflakes

def macros():
    template = get_renderer(
        'substanced.sdi.views:templates/master.pt').implementation()
    return {'master':template}

def breadcrumbs(request):
    breadcrumbs = []
    for resource in reversed(list(lineage(request.context))):
        if not has_permission('sdi.view', resource, request):
            return []
        url = request.mgmt_path(resource, '@@manage_main')
        name = resource.__name__ or 'Home'
        icon = request.registry.content.metadata(resource, 'icon')
        active = resource is request.context and 'active' or None
        breadcrumbs.append({'url':url, 'name':name, 'active':active,
                            'icon':icon})
    return breadcrumbs

def get_sdi_title(request):
    for location in lineage(request.context):
        sdi_title = getattr(location, 'sdi_title', None)
        if sdi_title is not None:
            return sdi_title
    return 'Substance D'

@subscriber(BeforeRender)
def add_renderer_globals(event):
   event['sdi_h'] = sys.modules[__name__]

