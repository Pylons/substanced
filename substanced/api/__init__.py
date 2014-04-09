import venusian

from pyramid.util import action_method, viewdefaults

API_ROUTE_NAME = 'substanced_api'


@viewdefaults
@action_method
def add_api_view(
    config,
    view=None,
    name="",
    permission="api.view",
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
    **predicates
    ):
    """ A :term:`configurator` which defines an ``API view``.

    This is a thin wrapper around :class:`pyramid.view.view_config`
    and accepts the same arguments.

    However it has different defaults. The `route_name` defaults
    to ``substanced_api``, the `renderer` defaults to ``json``,
    and the `permission` defaults to ``api.view``.
    """

    route_name = API_ROUTE_NAME
    config.add_view(
        view=view,
        name=name,
        permission=permission,
        route_name=route_name,
        request_method=request_method,
        request_param=request_param,
        containment=containment,
        attr=attr,
        renderer=renderer if renderer else 'json',
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
        content=True,
        **predicates
        )


class api_view(object):
    """ A :term:`decorator` which, when applied to a class or function,
    will configure it as an :term:`API view`.

    This is a thin wrapper around ``substanced.api.add_api_view``
    and accepts the same arguments.
    """
    venusian = venusian
    def __init__(self, **settings):
        self.__dict__.update(settings)

    def __call__(self, wrapped):
        settings = self.__dict__.copy()

        def callback(context, name, ob):
            config = context.config.with_package(info.module)
            # was "substanced.api" included?
            #add_api_view = getattr(config, 'add_api_view', None)
            add_api_view = config.add_api_view
            if add_api_view is not None:
                add_api_view(view=ob, **settings)

        info = self.venusian.attach(wrapped, callback, category='substanced')

        if info.scope == 'class':
            # if the decorator was attached to a method in a class, or
            # otherwise executed at class scope, we need to set an
            # 'attr' into the settings if one isn't already in there
            if settings.get('attr') is None:
                settings['attr'] = wrapped.__name__

        settings['_info'] = info.codeinfo # fbo "action_method"
        return wrapped


class _IsContentPredicate(object):

    def __init__(self, val, config):
        self.val = bool(val)
        self.registry = config.registry

    def text(self):
        return 'content = %s' % self.val

    phash = text

    def __call__(self, context, request):
        is_content = self.registry.content.typeof(context) is not None
        return is_content == self.val


def includeme(config):
    settings = config.registry.settings
    api_prefix = settings.get('substanced.api_prefix', '/sdapi')
    api_pattern = api_prefix + "*traverse"
    config.add_route(API_ROUTE_NAME, api_pattern)
    config.add_view_predicate('content', _IsContentPredicate)
    config.add_directive('add_api_view', add_api_view, action_wrap=False)
    config.scan()
