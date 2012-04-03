from pyramid.session import UnencryptedCookieSessionFactoryConfig
from pyramid.traversal import resource_path_tuple

from pyramid_deform import CSRFSchema as Schema # API
Schema = Schema # for pyflakes

from ..interfaces import IContent

def add_mgmt_view(config, *arg, **kw):
    kw['route_name'] = 'substanced_manage'
    config.add_view(*arg, **kw)

class mgmt_path(object):
    def __init__(self, request):
        self.request = request

    def __call__(self, obj, *arg, **kw):
        traverse = resource_path_tuple(obj)
        kw['traverse'] = traverse
        return self.request.route_path('substanced_manage', *arg, **kw)

def includeme(config):
    settings = config.get_settings()
    secret = settings['substanced.session_secret']
    session_factory = UnencryptedCookieSessionFactoryConfig(secret)
    config.set_session_factory(session_factory)
    config.add_directive('add_mgmt_view', add_mgmt_view)
    config.add_static_view('deformstatic', 'deform:static', cache_max_age=3600)
    config.add_static_view('sdistatic', 'substanced.sdi:static', 
                           cache_max_age=3600)
    config.add_route('substanced_manage', '/manage*traverse')
    config.add_mgmt_view('.views.PropertiesView', context=IContent,
                         name='properties', renderer='templates/form.pt')
    config.set_request_property(mgmt_path, reify=True)
    config.include('deform_bootstrap')
