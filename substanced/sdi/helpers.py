import sys

from pyramid.renderers import get_renderer

from pyramid.events import (
    subscriber,
    BeforeRender,
    )

from . import sdi_mgmt_views # API used by templates
sdi_mgmt_views = sdi_mgmt_views # pyflakes

def macros(): # XXX deprecate
    template = get_renderer(
        'substanced.sdi.views:templates/master.pt').implementation()
    return {'master':template}

def breadcrumbs(request): # XXX deprecate
    return request.sdiapi.breadcrumbs()

def get_sdi_title(request): # XXX deprecate
    return request.sdiapi.sdi_title()

@subscriber(BeforeRender)
def add_renderer_globals(event): # XXX deprecate
   event['sdi_h'] = sys.modules[__name__]

