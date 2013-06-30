from pyramid.view import view_defaults
from substanced.sdi import mgmt_view
from substanced.util import get_oid

from . import AuditScribe

@view_defaults(
    permission='sdi.view-auditlog',
    http_cache=0,
    )
class AuditLogEventStreamView(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request

    @mgmt_view(name='auditstream-sse', tab_condition=False)
    def sse_auditstream(self):
        if self.request.GET.get('contextonly'):
            oids = [get_oid(self.context)]
        else:
            oids = map(int, self.request.GET.getall('oid'))
        response = self.request.response
        response.content_type = 'text/event-stream'
        last_event_id = self.request.headers.get('Last-Event-Id')
        scribe = AuditScribe(self.context)
        if not last_event_id:
            # first call, set a baseline event id
            gen, idx = scribe.latest_id()
            response.text = compose_message('%s-%s' % (gen, idx))
            return response
        else:
            gen, idx = map(int, last_event_id.split('-', 1))
            events = scribe.newer(gen, idx, oids=oids)
            for gen, idx, event in events:
                event_id = '%s-%s' % (gen, idx)
                message = compose_message(event_id, event.name, event.payload)
                response.text += message
        return response

def compose_message(eventid, name=None, payload=''):
    msg = 'id: %s\n' % eventid
    if name:
        msg += 'event: %s\n' % name
    msg += 'data: %s\n\n' % payload
    return msg.decode('utf-8')

