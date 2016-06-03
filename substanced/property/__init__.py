import colander

from zope.interface import (
    implementer,
    Interface,
    )

from pyramid.compat import is_nonstr_iter
from pyramid.config.util import action_method
from walkabout import IPredicateDomain
from walkabout import PredicateDomain

from ..interfaces import IPropertySheet
from ..event import ObjectModified
from ..content import _ContentTypePredicate

_marker = object()

@implementer(IPropertySheet)
class PropertySheet(object):
    """ Convenience base class for concrete property sheet implementations """

    # XXX probably should be decorator for set and get
    permissions = (
        ('view', 'sdi.view'),
        ('change', 'sdi.edit-properties'),
        )

    schema = None

    extra_js_url = None

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def get(self):
        context = self.context
        result = {}
        for child in self.schema:
            name = child.name
            val = getattr(context, name, colander.null)
            result[name] = val
        return result

    def set(self, struct, omit=()):
        if not is_nonstr_iter(omit):
            omit = (omit,)
        changed = False
        for child in self.schema:
            name = child.name
            if (name in struct) and not (name in omit):
                # avoid setting an attribute on the object if it's the same
                # value as the existing value to avoid database bloat
                existing_val = getattr(self.context, name, _marker)
                new_val = struct[name]
                if existing_val != new_val:
                    setattr(self.context, name, new_val)
                    changed = True
        return changed

    def before_render(self, form): #pragma NO COVER
        """ Hook:  allow subclasses to scribble on form.

        Called by ``substanced.property.views.PropertySheetsView.before``,
        after building the form but before rendering it.
        """

    def after_set(self, changed):
        if changed is not False:
            event = ObjectModified(self.context)
            self.request.registry.subscribers((event, self.context), None)

def is_propertied(context, request):
    sheets = request.registry.content.metadata(context, 'propertysheets', None)
    if sheets is None:
        domain = get_domain(request.registry)
        sheets = list(domain.all(context, request))
    return len(sheets) > 0

class _PropertiedPredicate(object):
    is_propertied = staticmethod(is_propertied) # for testing
    
    def __init__(self, val, config):
        self.val = bool(val)
        self.registry = config.registry

    def text(self):
        return 'propertied = %s' % self.val

    phash = text

    def __call__(self, context, request):
        return self.is_propertied(context, request) == self.val

def get_domain(registry):
    domain = registry.queryUtility(IPredicateDomain, name='propertysheets')
    if domain is None:
        domain = PredicateDomain(IPropertySheet, registry)
        registry.registerUtility(domain, IPredicateDomain,
                                        name='propertysheets')
    return domain

@action_method
def add_propertysheet(config, name, propsheet, iface=None, **predicates):
    """Add a propertysheet for the content types implied by ``iface`` and
    ``predicates``.

    The ``propsheet`` argument represents a propertysheet class (or a
    :term:`dotted Python name` which identifies such a class); it will be
    called with two objects: ``context`` and ``request`` whenever Substance D
    determines that the propertysheet is necessary to display.  The ``iface``
    may be an :term:`interface` or a class or a :term:`dotted Python name` to a
    global object representing an interface or a class.

    Using the default ``iface`` value, ``None`` will cause the propertysheet
    to be registered for all content types.

    Any number of predicate keyword arguments may be passed in
    ``**predicates``.  Each predicate named will narrow the set of
    circumstances in which the propertysheet will be invoked.  Each named
    predicate must have been registered via
    :meth:`pyramid.config.Configurator.add_propertysheet_predicate` before it
    can be used.
    """
    iface = config.maybe_dotted(iface)
    if iface is None:
        iface = Interface

    def register():
        domain = get_domain(config.registry)
        domain.add_candidate(propsheet, iface, Interface, name=name,
                             **predicates)

    intr = config.introspectable(
        'property sheets',
        id(propsheet),
        config.object_description(propsheet),
        'property sheet'
        )

    intr['propsheet'] = propsheet
    intr['interfaces'] = iface

    config.action(None, register, introspectables=(intr,))
    return propsheet

@action_method
def add_propertysheet_predicate(config, name, factory,
                                before=None, after=None):
        """
        Adds a property sheet predicate factory.  The associated property sheet
        predicate can later be named as a keyword argument to
        :meth:`pyramid.config.Configurator.add_propertysheet` in the
        ``**predicates`` anonymous keyword argument dictionary.

        ``name`` should be the name of the predicate.  It must be a valid
        Python identifier (it will be used as a ``**predicates`` keyword
        argument to :meth:`~pyramid.config.Configurator.add_propertysheet`).

        ``factory`` should be a :term:`predicate factory` or :term:`dotted
        Python name` which refers to a predicate factory.

        """
        domain = get_domain(config.registry)
        domain.add_predicate(
            name,
            factory,
            before=before,
            after=after
            )
    

def includeme(config): # pragma: no cover
    config.add_view_predicate('propertied', _PropertiedPredicate)
    config.add_directive('add_propertysheet', add_propertysheet)
    config.add_directive('add_propertysheet_predicate',
                         add_propertysheet_predicate)
    config.add_propertysheet_predicate('content_type', _ContentTypePredicate)
