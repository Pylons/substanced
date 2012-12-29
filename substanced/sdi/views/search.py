from ..import mgmt_view

class SearchViews(object):
    def __init__(self, request):
        self.request = request

    @mgmt_view(
        name='search',
        permission='sdi.sdi.manage-contents',
        tab_condition=False,
        renderer='json'
    )
    def search(self):
        request = self.request
        query = request.params['query']

        results = [
            dict(label='Alabama', url='http://google.com/'),
            dict(label='Arkansas', url='http://mozilla.org/'),
            dict(label='Arizona', url='http://sun.com/'),
            dict(label='Alaska', url='http://cnet.com/'),
            dict(label='Kentucky', url='http://agendaless.com/'),
            dict(label='Virginia', url='http://mercury.com/'),
        ]
        return results
