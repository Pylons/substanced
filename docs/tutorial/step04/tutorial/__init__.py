from pyramid.config import Configurator

from substanced.site import Site


def main(global_config, **settings):
    config = Configurator(settings=settings,
                          root_factory=Site.root_factory)
    config.include('substanced')
    config.scan()
    return config.make_wsgi_app()
