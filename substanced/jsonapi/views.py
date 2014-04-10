from . import jsonapi_view
from pyramid.httpexceptions import (
    HTTPNoContent,
    HTTPForbidden,
    )
from pyramid.security import (
    has_permission,
    NO_PERMISSION_REQUIRED,
    )
from pyramid.view import view_defaults


@jsonapi_view(context=Exception, permission=NO_PERMISSION_REQUIRED)
def jsonapi_exception_view(exc, request):
    request.response.status_int = 500
    return {'error': str(exc)}


@view_defaults(content=True)
class ContentPropertiesAPI(object):

    def __init__(self, context, request):
        self.context = context
        self.request = request

    def _has_permission_to(self, perm, sheet_factory):
        permissions = getattr(sheet_factory, 'permissions', None)
        if permissions is not None:
            permission = dict(permissions).get(perm)
            if permission:
                return has_permission(permission, self.context, self.request)
        return True

    def _sheet_factories(self, action='view'):
        L = []
        candidates = self.request.registry.content.metadata(
            self.context, 'propertysheets', [])
        for name, factory in candidates:
            if not self._has_permission_to(action, factory):
                continue
            L.append((name, factory))
        return L

    @jsonapi_view(request_method='GET')
    def get(self):
        res = {}
        for name, factory in self._sheet_factories('view'):
            sheet = factory(self.context, self.request)
            appstruct = sheet.get()
            cstruct = sheet.schema.serialize(appstruct)
            res[name] = cstruct
        return res

    @jsonapi_view(request_method='PUT', permission='sdi.edit-properties')
    def update(self):
        data = self.request.json_body
        sheet_factories = dict(self._sheet_factories('change'))
        for name, cstruct in data.items():
            if name in sheet_factories:
                sheet = sheet_factories[name](self.context, self.request)
                appstruct = sheet.schema.deserialize(cstruct)
                sheet.set(appstruct)
            else:
                raise HTTPForbidden('Not allowed to update property sheet.')
        return HTTPNoContent()

    @jsonapi_view(request_method='DELETE', permission='sdi.manage-contents')
    def delete(self):
        # XXX should check __sdi_deletable__
        del self.context.__parent__[self.context.__name__]
        return HTTPNoContent()
