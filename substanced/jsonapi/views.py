from . import jsonapi_view
from pyramid.httpexceptions import HTTPNoContent
from substanced.property.views import PropertySheetsView


class ContentPropertiesAPI(object):

    def __init__(self, context, request):
        self.context = context
        self.request = request

    @jsonapi_view()
    def get(self):
        res = {}
        propview = PropertySheetsView(self.request)
        for name, factory in propview.viewable_sheet_factories():
            sheet = factory(self.context, self.request)
            appstruct = sheet.get()
            cstruct = sheet.schema.serialize(appstruct)
            res[name] = cstruct
        return res

    @jsonapi_view(request_method='DELETE', permission='sdi.manage-contents')
    def delete(self):
        # XXX should check __sdi_deletable__
        del self.context.__parent__[self.context.__name__]
        return HTTPNoContent()
