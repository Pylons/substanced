from pyramid.security import has_permission
from pyramid.httpexceptions import HTTPFound

from ...interfaces import IFolder

from ..helpers import get_batchinfo
from .. import mgmt_view

@mgmt_view(context=IFolder, name='contents', renderer='templates/contents.pt')
def folder_contents(context, request):
    if 'form.delete' in request.POST:
        todelete = request.POST.getall('delete')
        for name in todelete:
            v = context.get(name)
            if v is not None:
                if has_permission('delete', v, request):
                    del context[name]
        return HTTPFound(request.url)
    
    L = []
    for k, v in context.items():
        if has_permission('delete', v, request):
            L.append((k, v))
    batchinfo = get_batchinfo(L, request, url=request.url)
    return dict(batchinfo=batchinfo)

            
