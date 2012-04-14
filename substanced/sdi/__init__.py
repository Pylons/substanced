import math
import inspect
import operator
import urlparse

from zope.interface.interfaces import IInterface

from pyramid.config.views import viewdefaults
from pyramid.config.util import action_method

import venusian

from pyramid.authentication import SessionAuthenticationPolicy
from pyramid.exceptions import ConfigurationError
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.security import authenticated_userid
from pyramid.compat import is_nonstr_iter
from pyramid.traversal import resource_path_tuple
from pyramid.httpexceptions import (
    HTTPFound,
    HTTPBadRequest,
    )
from pyramid.session import UnencryptedCookieSessionFactoryConfig
from pyramid.view import view_config
from pyramid.interfaces import IView
from pyramid.request import Request

from ..service import find_service
from ..principal import groupfinder

MANAGE_ROUTE_NAME = 'substanced_manage'

def as_sorted_tuple(val):
    if not is_nonstr_iter(val):
        val = (val,)
    val = tuple(sorted(val))
    return val

def check_csrf_token(request):
    if request.params['csrf_token'] != request.session.get_csrf_token():
        raise HTTPBadRequest('incorrect CSRF token')

@viewdefaults
@action_method
def add_mgmt_view(
        config, view=None, name="", permission=None, request_method=None,
        request_param=None, containment=None, attr=None, renderer=None, 
        wrapper=None, xhr=False, accept=None, header=None, path_info=None, 
        custom_predicates=(), context=None, decorator=None, mapper=None, 
        http_cache=None, match_param=None, request_type=None, tab_title=None,
        tab_condition=None,
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
        
    route_name = MANAGE_ROUTE_NAME
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
    intr['tab_title'] = tab_title
    intr['tab_condition'] = tab_condition
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

class mgmt_view(view_config):
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
                 match_param=default, tab_title=default, tab_condition=default):
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

@mgmt_view(tab_title='manage_main')
def manage_main(request):
    view_data = get_mgmt_views(request)
    if not view_data:
        request.session['came_from'] = request.url
        return HTTPFound(location=request.mgmt_path(request.root, '@@login'))
    view_name = view_data[0]['view_name']
    return HTTPFound(request.mgmt_path(request.context, '@@%s' % view_name))

def get_user(request):
    userid = authenticated_userid(request)
    if userid is None:
        return None
    objectmap = find_service(request.context, 'objectmap')
    return objectmap.object_for(userid)

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
        if tab_condition is not None and names is None:
            if tab_condition is False or not tab_condition(request):
                continue
        for intr in related:
            view_name = intr['name']
            if view_name == '' and tab_title == 'manage_main':
                continue # manage_main view
            if names is not None and not view_name in names:
                continue
            if intr.category_name == 'views' and not view_name in L:
                derived = intr['derived_callable']
                # do a passable job at figuring out whether, if we visit the
                # url implied by this view, we'll be permitted to view it and
                # something reasonable will show up
                if IInterface.providedBy(intr['context']):
                    if not intr['context'].providedBy(context):
                        continue
                elif intr['context'] and not isinstance(
                        context, intr['context']):
                    continue
                req.path_info = request.mgmt_path(context, view_name)
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
    selected = []
    extra = []
    
    if hasattr(context, '__tab_order__'):
        tab_order = context.__tab_order__
        for view_data in L:
            for view_name in tab_order:
                if view_name == view_data['view_name']:
                    selected.append(view_data)
                    break
            else:
                extra.append(view_data)
    else:
        extra = L
                
    return selected + sorted(extra, key=operator.itemgetter('tab_title'))

def merge_url(url, **kw):
    segments = urlparse.urlsplit(url)
    extra_qs = [ '%s=%s' % (k, v) for (k, v) in 
                 urlparse.parse_qsl(segments.query, keep_blank_values=1) 
                 if k not in ('batch_size', 'batch_num')]
    qs = ''
    for k, v in sorted(kw.items()):
        qs += '%s=%s&' % (k, v)
    if extra_qs:
        qs += '&'.join(extra_qs)
    else:
        qs = qs[:-1]
    return urlparse.urlunsplit(
        (segments.scheme, segments.netloc, segments.path, qs, segments.fragment)
        )


def get_batchinfo(sequence, request, url=None, default_size=15):
    
    if url is None:
        url = request.url
        
    num = int(request.params.get('batch_num', 0))
    size = int(request.params.get('batch_size', default_size))

    if size:
        start = num * size
        end = start + size
        batch = sequence[start:end]
        last = int(math.ceil(len(sequence) / float(size)) - 1)
    else:
        start = 0
        end = 0
        batch = sequence
        last = 0
        
    first_url = None
    prev_url = None
    next_url = None
    last_url = None
    
    if num:
        first_url = merge_url(url, batch_size=size, batch_num=0)
    if start >= size:
        prev_url = merge_url(url, batch_size=size, batch_num=num-1)
    if len(sequence) > end:
        next_url = merge_url(url, batch_size=size, batch_num=num+1)
    if size and (num < last):
        last_url = merge_url(url, batch_size=size, batch_num=last)
    
    first_off = prev_off = next_off = last_off = ''
    
    if first_url is None:
        first_off = 'off'
    if prev_url is None:
        prev_off = 'off'
    if next_url is None:
        next_off = 'off'
    if last_url is None:
        last_off = 'off'
        
    return dict(batch=batch,
                required=prev_url or next_url,
                size=size,
                num=num,
                first_url=first_url,
                prev_url=prev_url,
                next_url=next_url,
                last_url=last_url,
                first_off=first_off,
                prev_off=prev_off,
                next_off=next_off,
                last_off=last_off,
                start=start,
                end=end,
                last=last)

YEAR = 86400 * 365

def includeme(config): # pragma: no cover
    config.add_directive('add_mgmt_view', add_mgmt_view, action_wrap=False)
    config.add_static_view('deformstatic', 'deform:static', cache_max_age=YEAR)
    config.add_static_view('sdistatic', 'substanced.sdi:static', 
                           cache_max_age=YEAR)
    manage_prefix = config.registry.settings.get(
        'substanced.manage_prefix', '/manage')
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
    authn_policy = SessionAuthenticationPolicy(callback=groupfinder)
    authz_policy = ACLAuthorizationPolicy()
    config.set_authentication_policy(authn_policy)
    config.set_authorization_policy(authz_policy)
    config.include('substanced.sdi.undo')
    config.scan('substanced.sdi')
