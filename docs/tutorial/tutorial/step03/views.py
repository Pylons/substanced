from pyramid.view import view_config

@view_config(renderer="templates/hello.pt")
def hello_view(request):
    manage_prefix = request.registry.settings.get(
        'substanced.manage_prefix', '/manage')
    return {'manage_prefix': manage_prefix}
