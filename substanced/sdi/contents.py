from pyramid.security import has_permission
from pyramid.httpexceptions import HTTPFound
from pyramid.httpexceptions import HTTPBadRequest

from substanced.interfaces import SERVICES_NAME

from ..interfaces import IFolder

from .helpers import get_batchinfo
from . import mgmt_view

@mgmt_view(context=IFolder, name='contents', renderer='templates/contents.pt',
           permission='view')
def folder_contents(context, request):
    if 'form.delete' in request.POST:
        if request.POST['csrf_token'] != request.session.get_csrf_token():
            raise HTTPBadRequest('Invalid CSRF token')
        todelete = request.POST.getall('delete')
        deleted = 0
        for name in todelete:
            v = context.get(name)
            if v is not None:
                if has_permission('delete', v, request):
                    del context[name]
                    deleted += 1
        request.session.flash('Deleted %s items' % deleted)
        return HTTPFound(request.referrer)
    
    L = []
    for k, v in context.items():
        if not has_permission('view', v, request):
            continue
        deletable = ( has_permission('delete', v, request) 
                      and not k == SERVICES_NAME 
                      and not context.__name__ == SERVICES_NAME)
        L.append((k, deletable))
    batchinfo = get_batchinfo(L, request, url=request.url)
    return dict(batchinfo=batchinfo)

            
