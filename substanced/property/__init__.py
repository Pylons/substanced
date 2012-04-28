from zope.interface import implementer

from pyramid.httpexceptions import (
    HTTPFound,
    HTTPForbidden,
    )
from pyramid.security import has_permission

from ..interfaces import (
    IPropertied,
    IPropertySheet,
    )
from ..form import FormView
from ..sdi import mgmt_view
from ..event import ObjectModified

def has_permission_to_view_any_propertysheet(context, request):
    sheet_factories = [ x[1] for x in context.__propsheets__ ]
    for sheet_factory in sheet_factories:
        permissions = getattr(sheet_factory, 'permissions', None)
        if not permissions:
            return True
        view_permission = dict(permissions).get('view')
        if view_permission:
            if has_permission(view_permission, context, request):
                return True
        else:
            return True
    return False

@mgmt_view(
    context=IPropertied,
    name='properties',
    renderer='templates/propertysheets.pt',
    tab_title='Properties',
    tab_condition=has_permission_to_view_any_propertysheet,
    permission='sdi.view',
    )
class PropertySheetsView(FormView):
    buttons = ('save',)
    
    def __init__(self, request):
        self.request = request
        self.context = request.context
        viewable_sheet_factories = self.viewable_sheet_factories()
        if not viewable_sheet_factories:
            raise HTTPForbidden('No viewable property sheets')
        subpath = request.subpath
        active_factory = None
        if subpath:
            active_sheet_name = subpath[0]
            active_factory = dict(viewable_sheet_factories).get(
                active_sheet_name)
        if not active_factory:
            active_sheet_name, active_factory = viewable_sheet_factories[0]
        self.active_sheet_name = active_sheet_name
        self.active_factory = active_factory
        self.active_sheet = active_factory(self.context, self.request)
        self.sheet_names = [x[0] for x in viewable_sheet_factories]
        self.schema = self.active_sheet.get_schema()

    def has_permission_to(self, perm, sheet_factory):
        permissions = getattr(sheet_factory, 'permissions', None)
        if permissions is not None:
            permission = dict(permissions).get(perm)
            if permission:
                return has_permission(permission, self.context, self.request)
        return True

    def viewable_sheet_factories(self):
        L = []
        for name, factory in self.context.__propsheets__:
            if not self.has_permission_to('view', factory):
                continue
            L.append((name, factory))
        return L

    def save_success(self, appstruct):
        if not self.has_permission_to('change', self.active_factory):
            raise HTTPForbidden(
                "You don't have permission to change properties of this "
                "property sheet")
        self.active_sheet.set(appstruct)
        self.active_sheet.after_set()
        return HTTPFound(self.request.mgmt_path(
            self.context, '@@properties', self.active_sheet_name))

    def show(self, form):
        readonly = not self.has_permission_to('change', self.active_factory)
        appstruct = self.active_sheet.get()
        return {'form':form.render(appstruct=appstruct, readonly=readonly)}

@implementer(IPropertySheet)
class PropertySheet(object):
    """ Convenience base class for concrete property sheet implementations """

    # XXX probably should be decorator for set and get
    permissions = (
        ('view', 'sdi.view'),
        ('change', 'sdi.edit-properties'),
        )

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def get_schema(self):
        return self.schema.bind(request=self.request)

    def get(self):
        context = self.context
        return dict(context.__dict__)

    def set(self, struct):
        for k in struct:
            setattr(self.context, k, struct[k])

    def after_set(self):
        event = ObjectModified(self.context)
        self.request.registry.subscribers((self.context, event), None)
        self.request.flash_undo('Updated properties', 'success')

def includeme(config): # pragma: no cover
    config.scan('.')
    
