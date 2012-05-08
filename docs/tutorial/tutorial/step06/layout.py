from pyramid.decorator import reify
from pyramid.renderers import get_renderer

class Layout(object):

    @reify
    def macros(self):
        fn = 'templates/global_layout.pt'
        template = get_renderer(fn).implementation()
        return template

