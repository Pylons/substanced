import sys

from pyramid.renderers import get_renderer
from pyramid.location import lineage
from pyramid.traversal import find_interface
from pyramid.security import has_permission

from pyramid.events import (
    subscriber,
    BeforeRender,
    )

from . import get_mgmt_views # API used by templates
get_mgmt_views = get_mgmt_views

from ..interfaces import ISite

def macros():
    template = get_renderer('templates/master.pt').implementation()
    return {'master':template}

def breadcrumbs(request):
    breadcrumbs = []
    for resource in reversed(list(lineage(request.context))):
        if not has_permission('sdi.view', resource, request):
            return []
        url = request.mgmt_path(resource)
        name = resource.__name__ or 'Home'
        icon = request.registry.content.metadata(resource, 'icon')
        active = resource is request.context and 'active' or None
        breadcrumbs.append({'url':url, 'name':name, 'active':active,
                            'icon':icon})
    return breadcrumbs

def get_site_title(request):
    site = find_interface(request.context, ISite)
    return site.title or 'Substance D'

@subscriber(BeforeRender)
def add_renderer_globals(event):
   event['h'] = sys.modules[__name__]

