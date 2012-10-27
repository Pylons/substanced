import inspect
import operator
import transaction

from pyramid_zodbconn import get_connection

from zope.interface.interfaces import IInterface

from pyramid.config.views import viewdefaults # XXX not an API
from pyramid.config.util import action_method # XXX not an API

import venusian

from pyramid.authentication import SessionAuthenticationPolicy
from pyramid.authorization import ACLAuthorizationPolicy
from pyramid.exceptions import ConfigurationError
from pyramid.registry import (
    predvalseq,
    Deferred,
    )
from pyramid.renderers import render
from pyramid.request import Request
from pyramid.security import (
    authenticated_userid,
    has_permission,
    )
from pyramid.session import UnencryptedCookieSessionFactoryConfig
from pyramid.traversal import resource_path_tuple

from ..objectmap import find_objectmap

MANAGE_ROUTE_NAME = 'substanced_manage'

_marker = object()

@viewdefaults
@action_method
def add_mgmt_view(
    config,
    view=None,
    name="",
    permission=None,
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
        'sdi views', discriminator, view_desc, 'sdi view')
    intr['tab_title'] = tab_title
    intr['tab_condition'] = tab_condition
    intr.relate('views', view_discriminator)
    config.action(discriminator, introspectables=(intr,))

def mgmt_path(request, obj, *arg, **kw):
    traverse = resource_path_tuple(obj)
    kw['traverse'] = traverse
    return request.route_path(MANAGE_ROUTE_NAME, *arg, **kw)

def mgmt_url(request, obj, *arg, **kw):
    traverse = resource_path_tuple(obj)
    kw['traverse'] = traverse
    return request.route_url(MANAGE_ROUTE_NAME, *arg, **kw)
    
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
    registry = request.registry
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
            L.append({'view_name': view_name,
                      'title': tab_title or view_name.capitalize(),
                      'class': css_class,
                      'url': request.mgmt_path(request.context,
                                               '@@%s' % view_name)
                     })

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
                    
    return ordered + sorted(L, key=operator.itemgetter('title'))

def sdi_folder_contents(folder, request):
    """
    Returns a sequence of dictionaries that can be used by a 'folder
    contents' view.  The sequence is implemented as a generator.  The
    ``folder`` object passed must implement the methods of the
    :class:`substanced.interfaces.IFolder` interface, and the ``request``
    object passed must be a Pyramid request.

    Each dictionary in the sequence reflects information about a single
    subobject in the folder.  Each dictionary in the sequence returned will
    have the following keys:

    ``name``

      The name of the subobject.

    ``deletable``

      A boolean indicating whether or not this subobject is deletable.

    ``viewable``

      A boolean indicating whether or not this subobject is viewable.

    ``url``

      The URL to the subobject.  This will be ``/path/to/subob/@@manage_main``.

    ``columns``

      The column values obtained from this subobject's attributes, as
      defined by the ``columns`` content-type hook (or the default columns,
      if no hook was supplied).

    This function considers a subobject:

    - 'deletable' if the user has the ``sdi.manage-contents`` permission on
      ``folder`` or if the subobject has a ``__sdi_deletable__`` attribute
      which resolves to a boolean ``True`` value.

    - 'viewable' if the user has the ``sdi.view`` permission against the
      subobject.

    This function honors two subobject hooks:: ``__sdi_hidden__``,
    and ``__sdi_deletable__``.

    The first subobject hook is named ``__sdi_hidden__``.  If a subobject has
    an attribute named ``__sdi_hidden__``, it is expected to be either a
    boolean or a callable.  If ``__sdi_hidden__`` is a boolean, the value is
    used verbatim.  If ``__sdi_hidden__`` is a callable, the callable is
    called with two positional arguments: the subobject and the request; the
    result is expected to be a boolean.  The ``__sdi_hidden__`` value (or
    callable return value) is used to determine whether or not the a
    dictionary is present which reflects the subobject in the sequence
    returned by this function.  If it is ``True``, a dictionary is not
    created for the subobject and will not present in the returned sequence.
    If it is ``False``, a dictionary *is* created for the subobject and will
    be present in the returned sequence.  If a subobject does not have the
    ``__sdi_hidden__`` attribute, it is assumed to be visible (not hidden) as
    if ``__sdi_hidden__`` was present and ``False``; in such a case a
    dictionary for the subobject will be present in the returned sequence.

    The second subobject hook is named ``__sdi_deletable__``.  It works just
    like ``__sdi_hidden__`` (it can be a bare value or a callable, and the
    callable is called just like ``__sdi_hidden__``).  If a subobject has an
    ``__sdi_deletable__`` attribute, and its resolved value is not ``None``,
    the value will used as the ``deletable`` value returned in the dictionary
    for the subobject.  If ``__sdi_deletable__`` does not exist on a subobject
    or resolves to ``None``, the ``deletable`` value will be the default: a
    boolean indicating whether the current user has the
    ``sdi.manage-contents`` permission on the ``folder``.

    This function honors two content type hooks: ``icon``, ``buttons``, and
    ``columns``.

    The first content type hook is named ``icon``.  If the ``icon`` supplied to
    the content type configuration of a subobject is a callable, the callable
    will be passed the subobject and the ``request``; it is expected to return
    an icon name or ``None``.  ``icon`` may alternately be either ``None`` or a
    string representing a icon name instead of a callable.

    The second content type hook is named ``buttons``.  The folder contents
    view is a good place to wire up application specific functionality that
    depends on content selection, so the button toolbar that shows up at the
    bottom of the page is customizable. The default buttons can be overridden
    by supplying a ``buttons`` keyword argument to the content type argument
    list.  It must be a callable object which accepts ``context, request,
    default_buttonspec`` and which returns a list of dictionaries; each
    dictionary represents a button or a button group.

    The ``buttons`` callable you supply will be passed the ``context`` and the
    ``request`` and ``buttonspec`` (a sequence of default button
    specifications). It must return a list of dictionaries representing button
    specifications with at least a ``type`` key for the button specification
    type and a ``buttons`` key with a list of dictionaries representing the
    buttons. The ``type`` should be one of the string values ``group`` or
    ``single``. A group will display its buttons side by side, with no margin,
    while the single type will display each button separately.

    Each button in a ``buttons`` dictionary is rendered using the button tag
    and requires five keys: ``id`` for the button's id attribute, ``name`` for
    the button's name attribute, ``class`` for any additional css classes to be
    applied to it, ``value`` for the value that will be passed as a request
    parameter when the form is submitted and ``text`` for the button's text.
    
    Most of the time, the best strategy will be to return a value containing
    the default buttonspec sequence passed in to the function (it will be a
    list).::

      def custom_buttons(context, request, default_buttonspec):
          custom_buttonspec = [{'type': 'single',
                               'buttons': [{'id': 'button1',
                                            'name': 'button1',
                                            'class': 'btn-primary',
                                            'value': 'button1',
                                            'text': 'Button 1'},
                                           {'id': 'button2',
                                            'name': 'button2',
                                            'class': 'btn-primary',
                                            'value': 'button2',
                                            'text': 'Button 2'}]}]
          return default_buttonspec + custom_buttonspec

      @content(
          'My Custom Folder',
          buttons=custom_buttons,
          )
      class MyCustomFolder(Persistent):
          pass

    Once the buttons are defined, a view needs to be registered to handle the
    new buttons. The view configuration has to set Folder as a context and
    include a ``request_param`` predicate with the same name as the ``value``
    defined for the corresponding button. The following template can be used
    to register such views, changing only the ``request_param`` value::

      @mgmt_view(
      context=IFolder,
      name='contents',
      renderer='substanced.sdi:templates/contents.pt',
      permission='sdi.manage-contents',
      request_method='POST',
      request_param='button1',
      tab_condition=False,
      )
      def button1(context, request):
          # add button functionality here, then go back to contents
          request.session.flash('Just did what button1 does')
          return HTTPFound(request.mgmt_path(context, '@@contents'))

    Note that context has to be IFolder for this to work. If you need to
    restrict a button to some specific list of content types, the Pyramid
    ``content_type`` predicate can be used.

    The third content-type hook is named ``columns``.  To display the contents
    using a table with any given subobject attributes, a callable named
    ``columns`` can be passed to a content type as metadata.  When the folder
    contents SDI view is invoked against an object of the type, the ``columns``
    callable will be passed the folder, a subobject the ``request``, and a set
    of default column specifications.  It will be called once for every object
    in the folder to obtain column representations for each of its subobjects.
    It must return a list of dictionaries with at least a ``name`` key for the
    column header and a ``value`` key with the correct column value given the
    subobject. The callable **must** be prepared to receive subobjects that
    will *not* have the desired attributes (the subobject passed will be
    ``None`` at least once in order for the system to compute headers).

    In addition to ``name`` and ``value``, the column dictionary can contain
    the keys ``sortable`` and ``filterable``, which specify respectively whether
    the column will have buttons for sorting the rows and whether a row can be
    filtered using a simple text search. The default value for both of those
    parameters is ``True``.

    Here's an example of using the ``columns`` content type hook::

      def custom_columns(folder, subobject, request, default_columnspec):
          return default_columnspec + [
              {'name': 'Review date',
               'value': getattr(subobject, 'review_date', ''),
               'sortable': True,
               'filterable': False},
              {'name': 'Rating',
               'value': getattr(subobject, 'rating', ''),
               'filterable': False,
               'sortable': True}
              ]

      @content(
          'My Custom Folder',
          columns=custom_columns,
          )
      class MyCustomFolder(Persistent):
          pass

    
    """
    can_manage = has_permission('sdi.manage-contents', folder, request)
    custom_columns = request.registry.content.metadata(
        folder, 'columns', _marker)
    for k, v in folder.items():
        hidden = getattr(v, '__sdi_hidden__', None)
        if hidden is not None:
            if callable(hidden):
                hidden = hidden(v, request)
        if not has_permission('sdi.view', v, request):
            hidden = True
        if hidden:
            continue
        icon = request.registry.content.metadata(v, 'icon')
        if callable(icon):
            icon = icon(v, request)
        deletable = getattr(v, '__sdi_deletable__', None)
        if deletable is not None:
            if callable(deletable):
                deletable = deletable(v, request)
        if deletable is None:
            deletable = can_manage
        url = request.mgmt_path(v, '@@manage_main')
        columns = default_sdi_columns(folder, v, request)
        if custom_columns is None:
            columns = []
        elif custom_columns is not _marker:
            columns = custom_columns(folder, v, request, columns)
        columns = [column['value'] for column in columns]
        data = dict(
            name=k,
            deletable=deletable,
            viewable=True, # XXX remove
            url=url,
            icon=icon,
            columns=columns,
            )
        yield data

def default_sdi_columns(folder, subobject, request):
    """ The default columns content-type hook """
    name = getattr(subobject, '__name__', '')
    url = request.mgmt_path(subobject, '@@manage_main')
    link_tag = '<a href="%s">%s</a>' % (url, name)
    icon = request.registry.content.metadata(subobject, 'icon')
    if callable(icon):
        icon = icon(subobject, request)
    icon_tag = '<i class="%s"> </i>' % icon
    return [
        {'name': 'Name',
         'value': '%s %s' % (icon_tag, link_tag),
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
              'class': 'btn-primary',
              'value': 'copy_finish',
              'text': 'Copy here'},
            {'id': 'cancel',
             'name': 'form.copy_finish',
             'class': 'btn-danger',
             'value': 'cancel',
             'text': 'Cancel'},
            ])

    if 'tomove' in request.session:
        finish_buttons.extend(
            [{'id': 'move_finish',
              'name': 'form.move_finish',
              'class': 'btn-primary',
              'value': 'move_finish',
              'text': 'Move here'},
             {'id': 'cancel',
              'name': 'form.move_finish',
              'class': 'btn-danger',
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
              'class': '',
              'value': 'rename',
              'text': 'Rename'},
              {'id': 'copy',
              'name': 'form.copy',
              'class': '',
              'value': 'copy',
              'text': 'Copy'},
              {'id': 'move',
              'name': 'form.move',
              'class': '',
              'value': 'move',
              'text': 'Move'},
              {'id': 'duplicate',
              'name': 'form.duplicate',
              'class': '',
              'value': 'duplicate',
              'text': 'Duplicate'}
              ]

        buttons.append({'type': 'group', 'buttons':main_buttons})

        delete_buttons = [
              {'id': 'delete',
               'name': 'form.delete',
               'class': 'btn-danger',
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
    objectmap = find_objectmap(request.context)
    return objectmap.object_for(userid)

class FlashUndo(object):
    
    get_connection = staticmethod(get_connection) # testing
    transaction = transaction # testing
    
    def __init__(self, request):
        self.request = request

    def __call__(self, msg, queue='', allow_duplicate=True):
        request = self.request
        conn = self.get_connection(request)
        db = conn.db()
        has_perm = has_permission('sdi.undo', request.context, request)
        if db.supportsUndo() and has_perm:
            hsh = str(id(request)) + str(hash(msg))
            t = self.transaction.get()
            t.note(msg)
            t.note('hash:'+hsh)
            csrf_token = request.session.get_csrf_token()
            query = {'csrf_token':csrf_token, 'hash':hsh}
            url = request.mgmt_path(request.context, '@@undo_one', _query=query)
            vars = {'msg':msg, 'url':url}
            button= render(
                'views/templates/undobutton.pt', vars, request=request)
            msg = button
        request.session.flash(msg, queue, allow_duplicate=allow_duplicate)

def include(config): # pragma: no cover
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
    config.add_request_method(mgmt_path)
    config.add_request_method(mgmt_url)
    config.add_request_method(get_user, name='user', reify=True)
    config.add_request_method(FlashUndo, name='flash_with_undo', reify=True)
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

def scan(config): # pragma: no cover
    config.scan('.')

def includeme(config): # pragma: no cover
    config.include(include)
    config.include(scan)
