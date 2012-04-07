from pyramid.config import Configurator
from substanced.models import Site
from pyramid.session import UnencryptedCookieSessionFactoryConfig

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings, root_factory=Site.root_factory)
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.include('substanced')
    secret = settings['substanced.secret']
    session_factory = UnencryptedCookieSessionFactoryConfig(secret)
    config.set_session_factory(session_factory)
    config.scan()
    return config.make_wsgi_app()
