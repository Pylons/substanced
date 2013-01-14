from ..import mgmt_view
from ...util import find_catalog

class SearchViews(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request

    def _query_results(self, query):
        request = self.request
        context = self.context
        query = query + '*'

        catalog = find_catalog(context, 'system')
        allowed = catalog['allowed']
        name = catalog['name']
        text = catalog['text']

        q = (allowed.allows(request, 'sdi.view') & text.eq(query))
        resultset = q.execute()
        resultset = resultset.sort(name)

        results = []
        for res_id in resultset.ids:
            res = resultset.resolver(res_id)
            url = request.sdiapi.mgmt_path(res, '@@manage_main')
            label = getattr(res, 'title', res.__name__)
            result = dict(label=label, url=url)
            results.append(result)

        return results

    @mgmt_view(
        name='search',
        permission='sdi.sdi.manage-contents',
        tab_condition=False,
        renderer='json'
    )
    def search(self):
        request = self.request
        query = request.params['query']
        return self._query_results(query)

    @mgmt_view(
        name='search',
        permission='sdi.sdi.manage-contents',
        tab_condition=False,
        request_param='results=1',
        renderer='templates/search_results.pt'
    )
    def search_results(self):
        request = self.request
        query = request.params['query']
        return {'results': self._query_results(query),
                'query': query}
