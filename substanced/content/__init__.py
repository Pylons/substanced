import inspect

from pyramid.threadlocal import get_current_registry

import venusian

_marker = object()

def get_content_type(resource, registry=None):
    if registry is None:
        registry = get_current_registry()
    return registry.content.typeof(resource)

def get_factory_type(resource):
    """ If the resource has a __factory_type__ attribute, return it.
    Otherwise return the full Python dotted name of the resource's class."""
    factory_type = getattr(resource, '__factory_type__', None)
    if factory_type is None:
        factory_type = dotted_name_of(resource.__class__)
    return factory_type

def dotted_name_of(g):
    name = g.__name__
    module = g.__module__
    return '.'.join((module, name))

class ContentRegistry(object):
    def __init__(self):
        self.factory_types = {}
        self.content_types = {}
        self.meta = {}

    def add(self, content_type, factory_type, factory, **meta):
        self.factory_types[factory_type] = content_type
        self.content_types[content_type] = factory
        self.meta[content_type] = meta

    def all(self):
        return list(self.content_types.keys())

    def create(self, content_type, *arg, **kw):
        factory = self.content_types[content_type]
        return factory(*arg, **kw)

    def metadata(self, context, name, default=None):
        content_type = self.typeof(context)
        maybe = self.meta.get(content_type, {}).get(name)
        if maybe is not None:
            return maybe
        return default

    def typeof(self, context):
        factory_type = get_factory_type(context)
        content_type = self.factory_types.get(factory_type)
        return content_type

    def istype(self, context, content_type):
        return content_type == self.typeof(context)

    def exists(self, content_type):
        return content_type in self.content_types.keys()

# venusian decorator that marks a class as a content class
class content(object):
    """ Use as a decorator for a content factory (usually a class).  Accepts
    a content type, a factory type (optionally), and a set of meta keywords."""
    venusian = venusian
    def __init__(self, content_type, factory_type=None, **meta):
        self.content_type = content_type
        self.factory_type = factory_type
        self.meta = meta

    def __call__(self, wrapped):
        def callback(context, name, ob):
            config = context.config.with_package(info.module)
            config.add_content_type(
                self.content_type, wrapped, factory_type=self.factory_type,
                **self.meta
                )
        info = self.venusian.attach(wrapped, callback, category='substanced')
        self.meta['_info'] = info.codeinfo # fbo "action_method"
        return wrapped

def add_content_type(config, content_type, factory, factory_type=None, **meta):
    """
    Configurator method which adds a content type.  Call via
    ``config.add_content_type`` during Pyramid configuration phase.
    
    ``content_type`` is a hashable object (usually a string) representing the
    content type.

    ``factory`` is a class or function which produces a content instance.  It
    must be a :term:`global object` (e.g. it cannot be a callable which is a
    method of a class or a callable instance).  If ``factory`` is a function
    rather than a class, a :term:`factory wrapper` is used (see below).

    ``**meta`` is an arbitrary set of keywords associated with the content
    type in the content registry.

    Some of the keywords in ``**meta`` have special meaning:

    - If ``meta`` contains the keyword ``propertysheets``, the content type
      will obtain a tab in the SDI that allows users to manage its
      properties.

    - If ``meta`` contains the keyword ``catalog`` and its value is true, the
      object will be tracked in the Substance D catalog.

    Other keywords in ``meta`` will just be stored, and have no special
    meaning.

    ``factory_type`` is an optional argument that can be used if the same
    factory must be used for two different content types; it is used during
    content type lookup (e.g. :func:`substanced.content.get_content_type`) to
    figure out which content type a constructed object is an instance of; it
    only needs to be used when the same factory is used for two different
    content types.  Note that two content types cannot have the same factory
    type, unless it is ``None``.

    If ``factory_type`` is passed, the supplied factory will be wrapped in a
    factory wrapper which adds a ``__factory_type__`` attribute to the
    constructed instance.  The value of this attribute will be used to
    determine the content type of objects created by the factory.

    If the factory is a function rather than a class, a factory wrapper is
    used unconditionally.

    The upshot wrt to ``factory_type``: if your factory is a class and you
    pass a ``factory_type`` *or* if your factory is a function, you won't be
    able to successfully use the 'bare' factory callable to construct an
    instance of this content in your code, because the resulting instance
    will not have a ``__factory_type__`` attribute.  Instead, you'll be
    required to use :meth:`substanced.content.Content.create` to create an
    instance of the object with a proper ``__factory_type__`` attribute.
    But if your factory is a class, and you don't pass ``factory_type``
    (the 'garden path'), you'll be able to use the class' constructor directly
    in your code to create instances of your content objects, which is more
    convenient and easier to unit test.
    
    """

    # NB: we don't want to make a content registration mutate the factory
    # it's using because folks may need to override content construction.
    # For example, they might use the same factory but an alternate set of
    # metainformation and we don't want the metainformation claimed by the
    # unused content registration to be jammed onto the factory (which will
    # be a global).  Therefore we derive a factory as possible using a
    # wrapper, but only if absolutely necessary (if the factory is a class
    # and a factory type is supplied, or if the factory is a function).  We
    # avoid wrapping the factory in the garden path case, because it's so
    # convenient to be able to use the factory directly (via an import) in
    # user code.
    
    factory_type, derived_factory = wrap_factory(factory, factory_type)

    def register_factory():
        config.registry.content.add(
            content_type, factory_type, derived_factory, **meta
            )

    discrim = ('sd-content-type', content_type)
    
    intr = config.introspectable(
        'substance d content types',
        discrim,
        content_type,
        'substance d content type',
        )
    intr['meta'] = meta
    intr['content_type'] = content_type
    intr['factory_type'] = factory_type
    intr['original_factory'] = factory
    intr['factory'] = derived_factory

    # conflict if two content type registrations have the same factory type
    config.action(('sd-factory-type', factory_type))
    
    config.action(discrim, callable=register_factory, introspectables=(intr,))

def wrap_factory(factory, factory_type):
    """ Wrap a factory in something that applies a factory type marker
    attribute to an instance created by the factory if necessary.  It's
    necessary if any of the following are true:

    - The factory is a class and factory_type is not None.

    - The factory is a function.

    If neither of these things is true, we return the factory unwrapped and
    return the dotted name of the factory as the factory name.
    """
 
    if inspect.isclass(factory) and factory_type is None:
        return dotted_name_of(factory), factory

    if factory_type is None:
        factory_type = dotted_name_of(factory)

    def factory_wrapper(*arg, **kw):
        inst = factory(*arg, **kw)
        inst.__factory_type__ = factory_type
        return inst
    
    factory_wrapper.__factory__ = factory
    return factory_type, factory_wrapper

class ContentTypePredicate(object):
    def __init__(self, val, config):
        self.val = val
        self.registry = config.registry

    def text(self):
        return 'content_type = %s' % (self.val,)

    phash = text

    def __call__(self, context, request):
        return get_content_type(context, self.registry) == self.val

def includeme(config): # pragma: no cover
    config.registry.content = ContentRegistry()
    config.add_directive('add_content_type', add_content_type)
    config.add_view_predicate('content_type', ContentTypePredicate)
