from . import jsonapi_view


class ContentPropertiesAPI(object):

    def __init__(self, context, request):
        self.context = context
        self.request = request

    @jsonapi_view()
    def get(self):
        return {"foo": "Hello World!"}
