from pyramid.config import Configurator
from pyramid.response import Response

# This acts as the view function
def hello_world(request):
    return Response('hello!')


def main(global_config, **settings):
    config = Configurator()
    config.add_view(hello_world)
    return config.make_wsgi_app()
