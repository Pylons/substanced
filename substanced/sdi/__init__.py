from pyramid.session import UnencryptedCookieSessionFactoryConfig

from pyramid_deform import CSRFSchema as Schema # API
Schema = Schema # for pyflakes

from ..interfaces import IContent

def includeme(config):
    settings = config.get_settings()
    secret = settings['substanced.session_secret']
    session_factory = UnencryptedCookieSessionFactoryConfig(secret)
    config.set_session_factory(session_factory)
    config.add_static_view('deformstatic', 'deform:static', cache_max_age=3600)
    config.add_static_view('sdistatic', 'substanced.sdi:static', 
                           cache_max_age=3600)
    config.add_route('substanced_manage', '/manage*traverse')
    config.add_view('substanced.sdi.views.PropertiesView',
                    context=IContent, route_name='substanced_manage',
                    renderer='substanced.sdi:templates/form.pt')
    config.include('deform_bootstrap')
