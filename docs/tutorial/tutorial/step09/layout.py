from pyramid.decorator import reify
from pyramid.renderers import get_renderer

class Layout(object):
    title = 'No Assigned Title'

    @reify
    def macros(self):
        fn = 'templates/global_layout.pt'
        template = get_renderer(fn).implementation()
        return {'layout': template}

    @reify
    def manage_prefix(self):
        settings = self.request.registry.settings
        return settings.get('substanced.manage_prefix',
                            '/manage')
