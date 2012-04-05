from pyramid.traversal import resource_path_tuple
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config

from pyramid_deform import CSRFSchema as Schema # API
Schema = Schema # for pyflakes

from pyramid.events import BeforeRender

from . import helpers

def add_mgmt_view(config, *arg, **kw):
    kw['route_name'] = 'substanced_manage'
    config.add_view(*arg, **kw)

class mgmt_path(object):
    def __init__(self, request):
        self.request = request

    def __call__(self, obj, *arg, **kw):
        traverse = resource_path_tuple(obj)
        kw['traverse'] = traverse
        return self.request.route_path(helpers.MANAGE_ROUTE_NAME, *arg, **kw)

class mgmt_view(view_config):
    """ A class :term:`decorator` which, when applied to a class, will
    provide defaults for all view configurations that use the class.  This
    decorator accepts all the arguments accepted by
    :class:`pyramid.config.view_config`, and each has the same meaning.

    See :ref:`view_defaults` for more information.
    """
    def __init__(self, *arg, **kw):
        view_config.__init__(self, *arg, **kw)
        self.route_name = helpers.MANAGE_ROUTE_NAME
    
def add_renderer_globals(event):
   event['h'] = helpers

def manage_main(request):
    view_names = helpers.get_mgmt_views(request)
    if not view_names:
        request.response.body = 'No management views for %s' % request.context
        return request.response
    return HTTPFound(request.mgmt_path(request.context, '@@%s' % view_names[0]))

@mgmt_view(name='testing', renderer='templates/testing.pt')
def testing(request):
    return {}
   
def includeme(config): # pragma: no cover
    config.add_directive('add_mgmt_view', add_mgmt_view)
    config.add_static_view('deformstatic', 'deform:static', cache_max_age=3600)
    config.add_static_view('sdistatic', 'substanced.sdi:static', 
                           cache_max_age=3600)
    config.add_route(helpers.MANAGE_ROUTE_NAME, '/manage*traverse')
    config.add_mgmt_view(manage_main, name='')
    config.scan('substanced.sdi')
    config.set_request_property(mgmt_path, reify=True)
    config.add_subscriber(add_renderer_globals, BeforeRender)
    config.include('deform_bootstrap')
