from pyramid.config import Configurator
from substanced.models import Site

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings, root_factory=Site.root_factory)
    config.add_static_view('static', 'static', cache_max_age=3600)
    config.include('substanced')
    config.scan()
    return config.make_wsgi_app()
