import transaction
import ZODB.POSException

from pyramid_zodbconn import get_connection
from pyramid.httpexceptions import HTTPFound

from .. import mgmt_view

class UndoViews(object):
    transaction = transaction # for tests

    def __init__(self, request):
        self.request = request

    @mgmt_view(
        name='undo_one',
        permission='sdi.undo',
        tab_condition=False, 
        check_csrf=True
        )
    def undo_one(self):
        request = self.request
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
                # provoke MultipleUndoErrors exception immediately
                msg = 'Undone: %s' % undo['clean_description']
                self.transaction.get().note(msg)
                self.transaction.commit() 
                request.session.flash(msg, 'success')
            except ZODB.POSException.POSError:
                self.transaction.abort()
                msg = 'Could not undo, sorry'
                request.session.flash(msg, 'error')
        return HTTPFound(
            request.referrer or request.sdiapi.mgmt_path(request.context)
            )
            
