import inspect
import venusian

from pyramid.compat import is_nonstr_iter
from pyramid.traversal import resource_path_tuple
from pyramid.httpexceptions import HTTPFound
from pyramid.view import view_config
from pyramid.interfaces import IView

from pyramid_deform import CSRFSchema as Schema # API
Schema = Schema # for pyflakes

from pyramid.events import BeforeRender

from . import helpers

def as_sorted_tuple(val):
    if not is_nonstr_iter(val):
        val = (val,)
    val = tuple(sorted(val))
    return val

def add_mgmt_view(
        config, view=None, name="", permission=None, request_method=None,
        request_param=None, containment=None, attr=None, renderer=None, 
        wrapper=None, xhr=False, accept=None, header=None, path_info=None, 
        custom_predicates=(), context=None, decorator=None, mapper=None, 
        http_cache=None, match_param=None, request_type=None
        ):
    view = config.maybe_dotted(view)
    context = config.maybe_dotted(context)
    containment = config.maybe_dotted(containment)
    mapper = config.maybe_dotted(mapper)
    decorator = config.maybe_dotted(decorator)

    if request_method is not None:
        request_method = as_sorted_tuple(request_method)
        if 'GET' in request_method and 'HEAD' not in request_method:
            # GET implies HEAD too
            request_method = as_sorted_tuple(request_method + ('HEAD',))
        
    route_name = helpers.MANAGE_ROUTE_NAME
    view_discriminator = [
        'view', context, name, request_type, IView, containment,
        request_param, request_method, route_name, attr,
        xhr, accept, header, path_info, match_param]
    view_discriminator.extend(sorted([hash(x) for x in custom_predicates]))
    view_discriminator = tuple(view_discriminator)

    discriminator = ('sdi view',) + view_discriminator[1:]

    if inspect.isclass(view) and attr:
        view_desc = 'method %r of %s' % (
            attr, config.object_description(view))
    else:
        view_desc = config.object_description(view)
    
    config.add_view(
        view=view, name=name, permission=permission, route_name=route_name,
        request_method=request_method, request_param=request_param,
        containment=containment, attr=attr, renderer=renderer, 
        wrapper=wrapper, xhr=xhr, accept=accept, header=header, 
        path_info=path_info, custom_predicates=custom_predicates, 
        context=context, decorator=decorator, mapper=mapper, 
        http_cache=http_cache, match_param=match_param, 
        request_type=request_type
        )
    
    intr = config.introspectable(
        'sdi views', discriminator, view_desc, 'sdi view')
    intr.relate('views', view_discriminator)
    config.action(discriminator, introspectables=(intr,))

class mgmt_path(object):
    def __init__(self, request):
        self.request = request

    def __call__(self, obj, *arg, **kw):
        traverse = resource_path_tuple(obj)
        kw['traverse'] = traverse
        return self.request.route_path(helpers.MANAGE_ROUTE_NAME, *arg, **kw)

class mgmt_view(view_config):
    """ A class :term:`decorator` which, when applied to a class, will
    provide defaults for all view configurations that use the class.  This
    decorator accepts all the arguments accepted by
    :class:`pyramid.config.view_config`, and each has the same meaning.

    See :ref:`view_defaults` for more information.
    """
    venusian = venusian
    def __call__(self, wrapped):
        settings = self.__dict__.copy()

        def callback(context, name, ob):
            config = context.config.with_package(info.module)
            config.add_mgmt_view(view=ob, **settings)

        info = self.venusian.attach(wrapped, callback, category='substanced')

        if info.scope == 'class':
            # if the decorator was attached to a method in a class, or
            # otherwise executed at class scope, we need to set an
            # 'attr' into the settings if one isn't already in there
            if settings.get('attr') is None:
                settings['attr'] = wrapped.__name__

        settings['_info'] = info.codeinfo # fbo "action_method"
        return wrapped
        
def add_renderer_globals(event):
   event['h'] = helpers

def manage_main(request):
    view_names = filter(None, helpers.get_mgmt_views(request))
    if not view_names:
        request.response.body = 'No management views for %s' % request.context
        return request.response
    return HTTPFound(request.mgmt_path(request.context, '@@%s' % view_names[0]))

def includeme(config): # pragma: no cover
    config.add_directive('add_mgmt_view', add_mgmt_view)
    config.add_static_view('deformstatic', 'deform:static', cache_max_age=3600)
    config.add_static_view('sdistatic', 'substanced.sdi:static', 
                           cache_max_age=3600)
    config.add_route(helpers.MANAGE_ROUTE_NAME, '/manage*traverse')
    config.add_mgmt_view(manage_main, name='')
    config.scan('substanced.sdi')
    config.set_request_property(mgmt_path, reify=True)
    config.add_subscriber(add_renderer_globals, BeforeRender)
    config.include('deform_bootstrap')
