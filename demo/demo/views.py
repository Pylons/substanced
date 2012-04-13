from pyramid.view import view_config

@view_config(renderer='templates/splash.pt')
def default_view(request):
    manage_prefix = request.registry.settings.get('substanced.manage_prefix', 
                                                  '/manage')
    return {'manage_prefix': manage_prefix}

