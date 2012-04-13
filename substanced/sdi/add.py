import operator

from pyramid.httpexceptions import HTTPFound

from ..interfaces import IFolder

from . import mgmt_view
from . import get_mgmt_views

def get_add_views(request, context=None):
    registry = request.registry
    if context is None:
        context = request.context
    introspector = registry.introspector

    candidates = {}
    
    for data in introspector.get_category('substance d content types'): 
        intr = data['introspectable']
        meta = intr['meta']
        viewname = meta.get('add_view')
        if viewname:
            typename = meta.get('name', intr['content_iface'].__name__)
            candidates[viewname] = typename

    candidate_names = candidates.keys()
    views = get_mgmt_views(request, context, names=candidate_names)

    L = []

    for view in views:
        view_name = view['view_name']
        url = request.mgmt_path(context, '@@' + view_name)
        L.append({'type_name':candidates[view_name], 'url':url})

    L.sort(key=operator.itemgetter('type_name'))

    return L

@mgmt_view(context=IFolder, name='add', tab_title='Add', 
           permission='add content', renderer='templates/add.pt')
def add_content(context, request):
    views = get_add_views(request, context)
    if len(views) == 1:
        return HTTPFound(location=views[0]['url'])
    return {'views':views}

