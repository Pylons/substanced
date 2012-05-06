from pyramid.config import Configurator
from substanced.site import Site

def main(global_config, **settings):
    """ This function returns a Pyramid WSGI application.
    """
    config = Configurator(settings=settings, root_factory=Site.root_factory)
    config.include('substanced')
    config.include('substanced.file')
    config.include('substanced.image')
    config.include('.catalog')
    config.scan()
    return config.make_wsgi_app()
