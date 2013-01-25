import inspect
import operator
import transaction

from pyramid_zodbconn import get_connection

from zope.interface.interfaces import IInterface

import venusian

from pyramid.authentication import SessionAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.decorator import reify
from pyramid.exceptions import ConfigurationError
from pyramid.location import lineage
from pyramid.registry import (
    predvalseq,
    Deferred,
    )
from pyramid.renderers import (
    render,
    get_renderer,
    )
from pyramid.request import Request
from pyramid.security import (
    authenticated_userid,
    has_permission,
    )
from pyramid.session import UnencryptedCookieSessionFactoryConfig
from pyramid.traversal import resource_path_tuple

from pyramid.util import (
    action_method,
    viewdefaults,
    TopologicalSorter,
    FIRST,
    LAST,
    Sentinel,
    )

LEFT = 'LEFT'
RIGHT = 'RIGHT'
MIDDLE = 'MIDDLE'

CENTER1 = Sentinel('CENTER1')
CENTER2 = Sentinel('CENTER2')

from ..objectmap import find_objectmap
from ..util import acquire

MANAGE_ROUTE_NAME = 'substanced_manage'

_marker = object()

@viewdefaults
@action_method
def add_mgmt_view(
    config,
    view=None,
    name="",
    permission='sdi.view',
    request_type=None,
    request_method=None,
    request_param=None,
    containment=None,
    attr=None,
    renderer=None, 
    wrapper=None,
    xhr=None,
    accept=None,
    header=None,
    path_info=None, 
    custom_predicates=(),
    context=None,
    decorator=None,
    mapper=None, 
    http_cache=None,
    match_param=None,
    tab_title=None,
    tab_condition=None,
    tab_before=None,
    tab_after=None,
    tab_near=None,
    **predicates
    ):
    
    view = config.maybe_dotted(view)
    context = config.maybe_dotted(context)
    containment = config.maybe_dotted(containment)
    mapper = config.maybe_dotted(mapper)
    decorator = config.maybe_dotted(decorator)

    route_name = MANAGE_ROUTE_NAME

    pvals = predicates.copy()
    pvals.update(
        dict(
            xhr=xhr,
            request_method=request_method,
            path_info=path_info,
            request_param=request_param,
            header=header,
            accept=accept,
            containment=containment,
            request_type=request_type,
            match_param=match_param,
            custom=predvalseq(custom_predicates),
            )
        )

    predlist = config.get_predlist('view')
    
    def view_discrim_func():
        # We need to defer the discriminator until we know what the phash
        # is.  It can't be computed any sooner because thirdparty
        # predicates may not yet exist when add_view is called.
        order, preds, phash = predlist.make(config, **pvals)
        return ('view', context, name, route_name, phash)

    def sdi_view_discrim_func():
        order, preds, phash = predlist.make(config, **pvals)
        return ('sdi view', context, name, route_name, phash)

    view_discriminator = Deferred(view_discrim_func)
    discriminator = Deferred(sdi_view_discrim_func)

    if inspect.isclass(view) and attr:
        view_desc = 'method %r of %s' % (attr, config.object_description(view))
    else:
        view_desc = config.object_description(view)

    config.add_view(
        view=view,
        name=name,
        permission=permission,
        route_name=route_name,
        request_method=request_method,
        request_param=request_param,
        containment=containment,
        attr=attr,
        renderer=renderer, 
        wrapper=wrapper,
        xhr=xhr,
        accept=accept,
        header=header, 
        path_info=path_info,
        custom_predicates=custom_predicates, 
        context=context,
        decorator=decorator,
        mapper=mapper, 
        http_cache=http_cache,
        match_param=match_param, 
        request_type=request_type,
        **predicates
        )
    
    intr = config.introspectable(
        'sdi views', discriminator, view_desc, 'sdi view'
        )

    if tab_near is not None:
        if tab_before or tab_after:
            raise ConfigurationError(
                'You cannot use tab_near and tab_before/tab_after together'
                )
        if tab_near == LEFT:
            tab_after = FIRST
            tab_before = CENTER1
        elif tab_near == MIDDLE:
            tab_after = CENTER1
            tab_before = CENTER2
        elif tab_near == RIGHT:
            tab_after = CENTER2
            tab_before = LAST
        else:
            raise ConfigurationError(
                'tab_near value must be one of LEFT, MIDDLE, RIGHT, or None'
                )

    intr['tab_title'] = tab_title
    intr['tab_condition'] = tab_condition
    intr['tab_before'] = tab_before
    intr['tab_after'] = tab_after
    intr['tab_near'] = tab_near

    intr.relate('views', view_discriminator)
    config.action(discriminator, introspectables=(intr,))

class mgmt_view(object):
    """ A class :term:`decorator` which, when applied to a class, will
    provide defaults for all view configurations that use the class.  This
    decorator accepts all the arguments accepted by
    :class:`pyramid.config.view_config`, and each has the same meaning.

    See :ref:`view_defaults` for more information.
    """
    venusian = venusian
    def __init__(self, **settings):
        self.__dict__.update(settings)
    
    def __call__(self, wrapped):
        settings = self.__dict__.copy()

        def callback(context, name, ob):
            config = context.config.with_package(info.module)
            # was "substanced.sdi" included?
            add_mgmt_view = getattr(config, 'add_mgmt_view', None)
            if add_mgmt_view is not None: 
                add_mgmt_view(view=ob, **settings)

        info = self.venusian.attach(wrapped, callback, category='substanced')

        if info.scope == 'class':
            # if the decorator was attached to a method in a class, or
            # otherwise executed at class scope, we need to set an
            # 'attr' into the settings if one isn't already in there
            if settings.get('attr') is None:
                settings['attr'] = wrapped.__name__

        settings['_info'] = info.codeinfo # fbo "action_method"
        return wrapped

def sdi_mgmt_views(context, request, names=None):
    if not hasattr(context, '__name__'):
        # shortcut if the context doesn't have a name (usually happens if the
        # context is an exception); we do this because mgmt_path uses Pyramid's
        # resource_path_tuple, which wants every object in the lineage to have
        # a __name__.
        return []

    registry = request.registry
    introspector = registry.introspector
    unordered = []

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
        tab_before = sdi_intr['tab_before']
        tab_after = sdi_intr['tab_after']
        def is_view(intr):
            return intr.category_name == 'views'
        for view_intr in filter(is_view, related):
            # NB: in reality, the above loop will execute exactly once because
            # each "sdi view" is associated with exactly one pyramid view
            view_name = view_intr['name']
            req.path_info = request.sdiapi.mgmt_path(context, view_name)
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
                if callable(tab_condition):
                    if not tab_condition(context, request):
                        continue
                elif not tab_condition:
                    continue
            derived = view_intr['derived_callable']
            if hasattr(derived, '__predicated__'):
                if not derived.__predicated__(context, req):
                    continue
            if hasattr(derived, '__permitted__'):
                if not derived.__permitted__(context, req):
                    continue
            if view_name == request.view_name:
                css_class = 'active'
            else:
                css_class = None
            unordered.append(
                {'view_name': view_name,
                 'tab_before':tab_before,
                 'tab_after':tab_after,
                 'title': tab_title or view_name.capitalize(),
                 'class': css_class,
                 'url': request.sdiapi.mgmt_path(
                     request.context, '@@%s' % view_name)
                 }
                )

    manually_ordered = []

    tab_order = request.registry.content.metadata(context, 'tab_order')
    
    if tab_order is not None:
        ordered_names = [ y for y in tab_order if y in
                          [ x['view_name'] for x in unordered ] ]
        for ordered_name in ordered_names:
            for view_data in unordered[:]:
                if view_data['view_name'] == ordered_name:
                    unordered.remove(view_data)
                    manually_ordered.append(view_data)

    # First sort non-manually-ordered views lexically by title. Reverse due to
    # the behavior of the toposorter; we'd like groups of things that share the
    # same before/after to be alpha sorted ascending relative to each other,
    # and reversing lexical ordering here gets us that behavior down the line.
    lexically_ordered = sorted(
        unordered,
        key=operator.itemgetter('title'),
        reverse=True,
        )

    # Then sort the lexically-presorted unordered views topologically based on
    # any tab_before and tab_after values in the view data.
    tsorter = TopologicalSorter(default_after=CENTER1, default_before=CENTER2)

    tsorter.add(
        CENTER1,
        None,
        after=FIRST,
        before=CENTER2,
        )

    tsorter.add(
        CENTER2,
        None,
        after=CENTER1,
        before=LAST,
        )

    for view_data in lexically_ordered:
        before=view_data.get('tab_before', None)
        after=view_data.get('tab_after', None)

        tsorter.add(
            view_data['view_name'],
            view_data,
            before=before,
            after=after,
            )

    topo_ordered = [
        x[1] for x in tsorter.sorted() if x[0] not in (CENTER1, CENTER2)
        ]

    return manually_ordered + topo_ordered

def default_sdi_columns(folder, subobject, request):
    """ The default columns content-type hook """
    name = getattr(subobject, '__name__', '')
    return [
        {'name': 'Name',
         'field': 'name',
         'value': name,
         'formatter': 'icon_label_url',
         'sortable': True}
        ]

def default_sdi_buttons(folder, request):
    """ The default buttons content-type hook """
    buttons = []
    finish_buttons = []

    if 'tocopy' in request.session:
        finish_buttons.extend(
            [
            {'id': 'copy_finish',
              'name': 'form.copy_finish',
              'class': 'btn-primary btn-sdi-act',
              'value': 'copy_finish',
              'text': 'Copy here'},
            {'id': 'cancel',
             'name': 'form.copy_finish',
             'class': 'btn-danger btn-sdi-act',
             'value': 'cancel',
             'text': 'Cancel'},
            ])

    if 'tomove' in request.session:
        finish_buttons.extend(
            [{'id': 'move_finish',
              'name': 'form.move_finish',
              'class': 'btn-primary btn-sdi-act',
              'value': 'move_finish',
              'text': 'Move here'},
             {'id': 'cancel',
              'name': 'form.move_finish',
              'class': 'btn-danger btn-sdi-act',
              'value': 'cancel',
              'text': 'Cancel'}])

    if finish_buttons:
        buttons.append(
          {'type':'single', 'buttons':finish_buttons}
          )

    if not 'tomove' in request.session and not 'tocopy' in request.session:

        main_buttons = [
             {'id': 'rename',
              'name': 'form.rename',
              'class': 'btn-sdi-del',
              'value': 'rename',
              'text': 'Rename'},
              {'id': 'copy',
              'name': 'form.copy',
              'class': 'btn-sdi-sel',
              'value': 'copy',
              'text': 'Copy'},
              {'id': 'move',
              'name': 'form.move',
              'class': 'btn-sdi-del',
              'value': 'move',
              'text': 'Move'},
              {'id': 'duplicate',
              'name': 'form.duplicate',
              'class': 'btn-sdi-sel',
              'value': 'duplicate',
              'text': 'Duplicate'}
              ]

        buttons.append({'type': 'group', 'buttons':main_buttons})

        delete_buttons = [
              {'id': 'delete',
               'name': 'form.delete',
               'class': 'btn-danger btn-sdi-del',
               'value': 'delete',
               'text': 'Delete'}
               ]

        buttons.append({'type': 'group', 'buttons':delete_buttons})

    return buttons

def default_sdi_addable(context, intr):
    meta = intr['meta']
    is_service = meta.get('is_service', False)
    if is_service:
        service_name = meta.get('service_name', None)
        return not (service_name and service_name in context)
    return True

def sdi_add_views(context, request):
    registry = request.registry
    introspector = registry.introspector

    candidates = {}
    
    for data in introspector.get_category('substance d content types'): 
        intr = data['introspectable']
        meta = intr['meta']
        content_type = intr['content_type']
        viewname = meta.get('add_view')
        if viewname:
            if callable(viewname):
                viewname = viewname(context, request)
                if not viewname:
                    continue
            addable_here = getattr(
                context,
                '__sdi_addable__',
                default_sdi_addable
                )
            if addable_here is not None:
                if callable(addable_here):
                    if not addable_here(context, intr):
                        continue
                else:
                    if not content_type in addable_here:
                        continue
            type_name = meta.get('name', content_type)
            icon = meta.get('icon', '')
            data = dict(type_name=type_name, icon=icon)
            candidates[viewname] = data

    candidate_names = candidates.keys()
    views = sdi_mgmt_views(context, request, names=candidate_names)

    L = []

    for view in views:
        view_name = view['view_name']
        url = request.sdiapi.mgmt_path(context, '@@' + view_name)
        data = candidates[view_name]
        data['url'] = url
        L.append(data)

    L.sort(key=operator.itemgetter('type_name'))

    return L

def user(request):
    userid = authenticated_userid(request)
    if userid is None:
        return None
    objectmap = find_objectmap(request.context)
    return objectmap.object_for(userid)

def mgmt_path(request, obj, *arg, **kw): # XXX deprecate
    return request.sdiapi.mgmt_path(obj, *arg, **kw)

def mgmt_url(request, obj, *arg, **kw): # XXX deprecate
    return request.sdiapi.mgmt_url(obj, *arg, **kw)

def flash_with_undo(request, *arg, **kw): # XXX deprecate
    return request.sdiapi.flash_with_undo(*arg, **kw)

class sdiapi(object):
    get_connection = staticmethod(get_connection) # testing
    transaction = transaction # testing
    sdi_mgmt_views = staticmethod(sdi_mgmt_views) # testing
    
    def __init__(self, request):
        self.request = request

    @reify
    def main_template(self):
        return get_renderer(
            'substanced.sdi.views:templates/master.pt').implementation()

    def get_flash_with_undo_snippet(self, msg, queue='', allow_duplicate=True):
        request = self.request
        conn = self.get_connection(request)
        db = conn.db()
        snippet = msg
        has_perm = has_permission('sdi.undo', request.context, request)
        if db.supportsUndo() and has_perm:
            hsh = str(id(request)) + str(hash(msg))
            t = self.transaction.get()
            t.note(msg)
            t.setExtendedInfo('undohash', hsh)
            csrf_token = request.session.get_csrf_token()
            query = {'csrf_token': csrf_token, 'undohash': hsh}
            url = self.mgmt_path(request.context, '@@undo_recent', _query=query)
            vars = {'msg': msg, 'url': url}
            button = render(
                'views/templates/undobutton.pt', vars, request=request)
            snippet = button
        return snippet

    def flash_with_undo(self, msg, queue='', allow_duplicate=True):
        request = self.request
        snippet = self.get_flash_with_undo_snippet(msg)
        request.session.flash(snippet, queue, allow_duplicate=allow_duplicate)

    def mgmt_path(self, obj, *arg, **kw):
        request = self.request
        traverse = resource_path_tuple(obj)
        kw['traverse'] = traverse
        return request.route_path(MANAGE_ROUTE_NAME, *arg, **kw)

    def mgmt_url(self, obj, *arg, **kw):
        request = self.request
        traverse = resource_path_tuple(obj)
        kw['traverse'] = traverse
        return request.route_url(MANAGE_ROUTE_NAME, *arg, **kw)

    def breadcrumbs(self):
        request = self.request
        breadcrumbs = []
        for resource in reversed(list(lineage(request.context))):
            if not has_permission('sdi.view', resource, request):
                return []
            url = request.sdiapi.mgmt_path(resource, '@@manage_main')
            name = resource.__name__ or 'Home'
            icon = request.registry.content.metadata(resource, 'icon')
            active = resource is request.context and 'active' or None
            breadcrumbs.append({'url':url, 'name':name, 'active':active,
                                'icon':icon})
        return breadcrumbs

    def sdi_title(self):
        return acquire(self.request.context, 'sdi_title', 'Substance D')

    def mgmt_views(self, context):
        return self.sdi_mgmt_views(context, self.request)

def includeme(config): # pragma: no cover
    settings = config.registry.settings
    YEAR = 86400 * 365
    config.add_directive('add_mgmt_view', add_mgmt_view, action_wrap=False)
    config.add_static_view('deformstatic', 'deform:static', cache_max_age=YEAR)
    config.add_static_view('sdistatic', 'substanced.sdi:static',
                           cache_max_age=YEAR)
    # b/c alias for template lookups
    config.override_asset(to_override='substanced.sdi:templates/',
                          override_with='substanced.sdi.views:templates/')
    manage_prefix = settings.get('substanced.manage_prefix', '/manage')
    manage_pattern = manage_prefix + '*traverse'
    config.add_route(MANAGE_ROUTE_NAME, manage_pattern)
    config.add_request_method(mgmt_path) # XXX deprecate
    config.add_request_method(mgmt_url) # XXX deprecate
    config.add_request_method(flash_with_undo) # XXX deprecate
    config.add_request_method(user, reify=True)
    config.add_request_method(sdiapi, reify=True)
    config.include('deform_bootstrap')
    secret = settings.get('substanced.secret')
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
