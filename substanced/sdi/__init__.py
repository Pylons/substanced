import inspect
import operator

from zope.interface.interfaces import IInterface

from pyramid.config.views import viewdefaults # XXX not an API
from pyramid.config.util import action_method # XXX not an API

import venusian

from pyramid.authentication import SessionAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.compat import is_nonstr_iter
from pyramid.exceptions import ConfigurationError
from pyramid.httpexceptions import HTTPBadRequest
from pyramid.interfaces import IView
from pyramid.security import authenticated_userid
from pyramid.request import Request
from pyramid.session import UnencryptedCookieSessionFactoryConfig
from pyramid.traversal import resource_path_tuple

from ..service import find_service

MANAGE_ROUTE_NAME = 'substanced_manage'

def as_sorted_tuple(val):
    if not is_nonstr_iter(val):
        val = (val,)
    val = tuple(sorted(val))
    return val

def check_csrf_token(request, token='csrf_token'):
    if request.params.get(token) != request.session.get_csrf_token():
        raise HTTPBadRequest('incorrect CSRF token')

@viewdefaults
@action_method
def add_mgmt_view(
        config, view=None, name="", permission=None, request_method=None,
        request_param=None, containment=None, attr=None, renderer=None, 
        wrapper=None, xhr=False, accept=None, header=None, path_info=None, 
        custom_predicates=(), context=None, decorator=None, mapper=None, 
        http_cache=None, match_param=None, request_type=None, tab_title=None,
        tab_condition=None, check_csrf=True, csrf_token='csrf_token',
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
        
    if check_csrf:
        def _check_csrf_token(context, request):
            check_csrf_token(request, csrf_token)
            return True
        custom_predicates = tuple(custom_predicates) + (_check_csrf_token,)
    
    route_name = MANAGE_ROUTE_NAME
    view_discriminator = [
        'view', context, name, request_type, IView, containment,
        request_param, request_method, route_name, attr,
        xhr, accept, header, path_info, match_param]
    view_discriminator.extend(sorted([hash(x) for x in custom_predicates]))
    view_discriminator = tuple(view_discriminator)

    discriminator = ('sdi view',) + view_discriminator[1:]

    if inspect.isclass(view) and attr:
        view_desc = 'method %r of %s' % (attr, config.object_description(view))
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
    intr['tab_title'] = tab_title
    intr['tab_condition'] = tab_condition
    intr['check_csrf'] = check_csrf
    intr['csrf_token'] = csrf_token
    intr.relate('views', view_discriminator)
    config.action(discriminator, introspectables=(intr,))

class mgmt_path(object):
    def __init__(self, request):
        self.request = request

    def __call__(self, obj, *arg, **kw):
        traverse = resource_path_tuple(obj)
        kw['traverse'] = traverse
        return self.request.route_path(MANAGE_ROUTE_NAME, *arg, **kw)

class _default(object):
    def __nonzero__(self):
        return False

    __bool__ = __nonzero__

    def __repr__(self): # pragma: no cover
        return '(default)'

default = _default()

class mgmt_view(object):
    """ A class :term:`decorator` which, when applied to a class, will
    provide defaults for all view configurations that use the class.  This
    decorator accepts all the arguments accepted by
    :class:`pyramid.config.view_config`, and each has the same meaning.

    See :ref:`view_defaults` for more information.
    """
    venusian = venusian
    def __init__(self, name=default, request_type=default, for_=default,
                 permission=default, route_name=default,
                 request_method=default, request_param=default,
                 containment=default, attr=default, renderer=default,
                 wrapper=default, xhr=default, accept=default,
                 header=default, path_info=default,
                 custom_predicates=default, context=default,
                 decorator=default, mapper=default, http_cache=default,
                 match_param=default, tab_title=default, tab_condition=default,
                 check_csrf=default, csrf_token=default):
        L = locals()
        if (context is not default) or (for_ is not default):
            L['context'] = context or for_
        for k, v in L.items():
            if k not in ('self', 'L') and v is not default:
                setattr(self, k, v)
    
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

def get_mgmt_views(request, context=None, names=None):
    registry = request.registry
    if context is None:
        context = request.context
    introspector = registry.introspector
    L = []

    # create a dummy request signaling our intent
    req = Request(request.environ.copy())
    req.script_name = request.script_name
    req.context = context
    req.matched_route = request.matched_route
    req.method = 'GET' 
    req.registry = request.registry

    for data in introspector.get_category('sdi views'): 
        related = data['related']
        sdi_intr = data['introspectable']
        tab_title = sdi_intr['tab_title']
        tab_condition = sdi_intr['tab_condition']
        def is_view(intr):
            return intr.category_name == 'views'
        for view_intr in filter(is_view, related):
            # NB: in reality, the above loop will execute exactly once because
            # each "sdi view" is associated with exactly one pyramid view
            view_name = view_intr['name']
            req.path_info = request.mgmt_path(context, view_name)
            if names is not None and not view_name in names:
                continue
            # do a passable job at figuring out whether, if we visit the
            # url implied by this view, we'll be permitted to view it and
            # something reasonable will show up
            intr_context = view_intr['context']
            if IInterface.providedBy(intr_context):
                if not intr_context.providedBy(context):
                    continue
            elif intr_context and not isinstance(context, intr_context):
                continue
            if tab_condition is not None and names is None:
                if tab_condition is False or not tab_condition(
                    context, request):
                    continue
            derived = view_intr['derived_callable']
            if hasattr(derived, '__predicated__'):
                if not derived.__predicated__(context, req):
                    continue
            if hasattr(derived, '__permitted__'):
                if not derived.__permitted__(context, req):
                    continue
            L.append(
                {'view_name':view_name,
                 'tab_title':tab_title or view_name.capitalize()}
                )

    ordered = []

    tab_order = request.registry.content.metadata(context, 'tab_order')
    
    if tab_order is not None:
        ordered_names_available = [ y for y in tab_order if y in
                                    [ x['view_name'] for x in L ] ]
        for ordered_name in ordered_names_available:
            for view_data in L:
                if view_data['view_name'] == ordered_name:
                    L.remove(view_data)
                    ordered.append(view_data)
                    
    return ordered + sorted(L, key=operator.itemgetter('tab_title'))

def get_add_views(request, context=None):
    registry = request.registry
    if context is None:
        context = request.context
    introspector = registry.introspector

    candidates = {}
    
    for data in introspector.get_category('substance d content types'): 
        intr = data['introspectable']
        meta = intr['meta']
        content_type = intr['content_type']
        viewname = meta.get('add_view')
        if viewname:
            addable_here = getattr(context, '__addable__', None)
            if addable_here is not None:
                if not content_type in addable_here:
                    continue
            type_name = meta.get('name', content_type)
            icon = meta.get('icon', '')
            data = dict(type_name=type_name, icon=icon)
            candidates[viewname] = data

    candidate_names = candidates.keys()
    views = get_mgmt_views(request, context, names=candidate_names)

    L = []

    for view in views:
        view_name = view['view_name']
        url = request.mgmt_path(context, '@@' + view_name)
        data = candidates[view_name]
        data['url'] = url
        L.append(data)

    L.sort(key=operator.itemgetter('type_name'))

    return L

def get_user(request):
    userid = authenticated_userid(request)
    if userid is None:
        return None
    objectmap = find_service(request.context, 'objectmap')
    return objectmap.object_for(userid)

def add_permission(config, permission_name):
    """ A configurator directive which registers a free-standing permission
    (without associating it with a view), so it shows up in the Security tab
    dropdown for permissions. Usage example::

      config = Configurator()
      config.add_permission('view')
    """
    intr = config.introspectable('permissions', permission_name,
                                 permission_name, 'permission')
    intr['value'] = permission_name
    config.action(None, introspectables=(intr,))

def includeme(config): # pragma: no cover
    config.add_directive('add_mgmt_view', add_mgmt_view, action_wrap=False)
    config.add_directive('add_permission', add_permission)
    YEAR = 86400 * 365
    config.add_static_view('deformstatic', 'deform:static', cache_max_age=YEAR)
    config.add_static_view('sdistatic', 'substanced.sdi:static', 
                           cache_max_age=YEAR)
    settings = config.registry.settings
    manage_prefix = settings.get('substanced.manage_prefix', '/manage')
    manage_pattern = manage_prefix + '*traverse'
    config.add_route(MANAGE_ROUTE_NAME, manage_pattern)
    config.set_request_property(mgmt_path, reify=True)
    config.set_request_property(get_user, name='user', reify=True)
    config.include('deform_bootstrap')
    secret = config.registry.settings.get('substanced.secret')
    if secret is None:
        raise ConfigurationError(
            'You must set a substanced.secret key in your .ini file')
    session_factory = UnencryptedCookieSessionFactoryConfig(secret)
    config.set_session_factory(session_factory)
    from ..principal import groupfinder
    authn_policy = SessionAuthenticationPolicy(callback=groupfinder)
    authz_policy = ACLAuthorizationPolicy()
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)
    config.add_permission('sdi.edit-properties') # used by property machinery
    config.scan('.')
