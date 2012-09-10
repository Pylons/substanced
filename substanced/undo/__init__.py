import transaction
import ZODB.POSException

from pyramid_zodbconn import get_connection

from pyramid.renderers import render
from pyramid.httpexceptions import HTTPFound
from pyramid.security import has_permission

from ..sdi import mgmt_view

class FlashUndo(object):
    
    get_connection = staticmethod(get_connection) # testing
    transaction = transaction # testing
    
    def __init__(self, request):
        self.request = request

    def __call__(self, msg, queue='', allow_duplicate=True):
        request = self.request
        conn = self.get_connection(request)
        db = conn.db()
        has_perm = has_permission('sdi.undo', request.context, request)
        if db.supportsUndo() and has_perm:
            hsh = str(id(request)) + str(hash(msg))
            t = self.transaction.get()
            t.note(msg)
            t.note('hash:'+hsh)
            csrf_token = request.session.get_csrf_token()
            query = {'csrf_token':csrf_token, 'hash':hsh}
            url = request.mgmt_path(request.context, '@@undo_one', _query=query)
            vars = {'msg':msg, 'url':url}
            button= render('templates/undobutton.pt', vars, request=request)
            msg = button
        request.session.flash(msg, queue, allow_duplicate=allow_duplicate)

@mgmt_view(name='undo_one', permission='sdi.undo', tab_condition=False, 
           check_csrf=True)
def undo_one(request):
    needle = 'hash:' + request.params['hash']
    undo = None
    conn = get_connection(request)
    db = conn.db()
    for record in db.undoInfo(): # by default, the last 20 transactions
        description = record['description']
        if needle in description:
            undo = dict(record)
            undo['clean_description'] = description.replace(needle, '')
            break
    if undo is None:
        request.session.flash('Could not undo, sorry', 'error')
    else:
        try:
            db.undo(undo['id'])
            msg = 'Undone: %s' % undo['clean_description']
            request.session.flash(msg, 'success')
        except ZODB.POSException.POSError:
            msg = 'Could not undo, sorry'
            request.session.flash(msg, 'error')
    return HTTPFound(request.referrer or request.mgmt_path(request.context))
            
def includeme(config): # pragma: no cover
    config.add_request_method(FlashUndo, name='flash_with_undo', reify=True)
    config.scan('.')
    
