from .resources import Blog
from pyramid.config import Configurator

def main(global_config, **settings):
    config = Configurator(settings=settings, root_factory=Blog.root_factory)
    config.include('substanced')
    config.add_permission('view')
    config.add_static_view('static', 'static', cache_max_age=86400)
    config.scan()
    return config.make_wsgi_app()
   
