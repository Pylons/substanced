import datetime
from logging import getLogger

from pyramid.view import view_defaults
from pyramid.compat import PY3, text_type
from substanced.sdi import mgmt_view, RIGHT
from substanced.util import get_oid
from colander.iso8601 import UTC

from . import AuditScribe

@view_defaults(
    permission='sdi.view-auditlog',
    http_cache=0,
    )
class AuditLogEventStreamView(object):
    AuditScribe = AuditScribe # for test replacement
    logger = getLogger('substanced')

    def __init__(self, context, request):
        self.context = context
        self.request = request

    @mgmt_view(
        name='auditing',
        tab_title='Auditing',
        renderer='templates/auditing.pt',
        tab_near=RIGHT,
        physical_path='/',
        )
    def auditing(self):
        scribe = self.AuditScribe(self.context)
        results = []
        for gen, idx, event in scribe:
            timestamp = event.timestamp
            time = datetime.datetime.fromtimestamp(timestamp, UTC).strftime(
                '%Y-%m-%d %H:%M:%S UTC')
            results.insert(0, (gen, idx, time, event))
        return {'results':results}

    @mgmt_view(name='auditstream-sse', tab_condition=False)
    def auditstream_sse(self):
        """Returns an event stream suitable for driving an HTML5 EventSource.
           The event stream will contain auditing events.

           Obtain events for the context of the view only::

            var source = new EventSource(
               "${request.sdiapi.mgmt_path(context, 'auditstream-sse')}");
           
           Obtain events for a single OID unrelated to the context::

            var source = new EventSource(
               "${request.sdiapi.mgmt_path(context, 'auditstream-sse', _query={'oid':'12345'})}");

           Obtain events for a set of OIDs::

            var source = new EventSource(
               "${request.sdiapi.mgmt_path(context, 'auditstream-sse', _query={'oid':['12345', '56789']})}");

           Obtain all events for all oids::

            var source = new EventSource(
               "${request.sdiapi.mgmt_path(context, 'auditstream-sse', _query={'all':'1'})}");
           
           The executing user will need to possess the ``sdi.view-auditstream``
           permission against the context on which the view is invoked.
        """
        request = self.request
        response = request.response
        response.content_type = 'text/event-stream'
        last_event_id = request.headers.get('Last-Event-Id')
        scribe = self.AuditScribe(self.context)
        if not last_event_id:
            # first call, set a baseline event id
            gen, idx = scribe.latest_id()
            msg = compose_message('%s-%s' % (gen, idx))
            response.text = msg
            self.logger.debug(
                'New SSE connection on %s, returning %s' % (
                    request.url, msg)
                )
            return response
        else:
            if request.GET.get('all'):
                oids = ()
            elif request.GET.get('oid'):
                oids = map(int, request.GET.getall('oid'))
            else:
                oids = [get_oid(self.context)]
            _gen, _idx = map(int, last_event_id.split('-', 1))
            events = scribe.newer(_gen, _idx, oids=oids)
            msg = text_type('')
            for gen, idx, event in events:
                event_id = '%s-%s' % (gen, idx)
                message = compose_message(event_id, event.name, event.payload)
                msg += message
            self.logger.debug(
                'SSE connection on %s with id %s-%s, returning %s' % (
                    request.url, _gen, _idx, msg)
                )
            response.text = msg
            return response

def compose_message(eventid, name=None, payload=''):
    msg = 'id: %s\n' % eventid
    if name:
        msg += 'event: %s\n' % name
    msg += 'data: %s\n\n' % payload
    if PY3: # pragma: no cover
        return msg
    else:
        return msg.decode('utf-8')

