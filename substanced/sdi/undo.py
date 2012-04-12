import transaction
import ZODB.POSException

from pyramid_zodbconn import get_connection

from pyramid.renderers import render
from pyramid.httpexceptions import HTTPFound

from . import mgmt_view
from .helpers import check_csrf_token

class FlashUndo(object):
    def __init__(self, request):
        self.request = request

    def __call__(self, msg):
        request = self.request
        conn = get_connection(request)
        db = conn.db()
        if db.supportsUndo():
            hsh = str(id(request)) + str(hash(msg))
            t = transaction.get()
            t.note(msg)
            t.note('hash:'+hsh)
            csrf_token = request.session.get_csrf_token()
            query = {'csrf_token':csrf_token, 'hash':hsh}
            url = request.mgmt_path(request.context, '@@undo_one', _query=query)
            vars = {'msg':msg, 'url':url}
            button= render('templates/undobutton.pt', vars, request=request)
            msg = button
        request.session.flash(msg)

@mgmt_view(name='undo_one', permission='undo', tab_condition=False)
def undo_one(request):
    check_csrf_token(request)
    needle = 'hash:' + request.params['hash']
    undo = None
    conn = get_connection(request)
    db = conn.db()
    for record in db.undoInfo():
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
            
def includeme(config):
    config.set_request_property(FlashUndo, name='flash_undo', reify=True)
