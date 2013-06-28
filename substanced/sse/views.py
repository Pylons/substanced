import time

from pyramid.view import view_defaults
from substanced.sdi import mgmt_view

from . import EventScribe

@view_defaults(
    permission='sdi.view-eventstream',
    http_cache=0,
    )
class EventStreamView(object):
    def __init__(self, context, request):
        self.context = context
        self.request = request

    @mgmt_view(name='eventstream', tab_condition=False)
    def eventstream(self):
        response = self.request.response
        response.content_type = 'text/event-stream'
        last_event_id = self.request.headers.get('Last-Event-Id')
        if not last_event_id:
            # first call, set a baseline event id
            response.text = compose_message(time.time())
            return response
        scribe = EventScribe(self.context)
        events = scribe.since(last_event_id)
        for event_time, (name, payload) in events:
            message = compose_message(event_time, name, payload)
            response.text += message
        return response

    @mgmt_view(name='show_events', renderer='templates/events.pt',
               tab_condition=False)
    def events(request):
        return {}

def compose_message(eventid, name=None, payload=''):
    msg = 'id: %s\n' % eventid
    if name:
        msg += 'event: %s\n' % name
    msg += 'data: %s\n\n' % payload
    return msg.decode('utf-8')

