import time
import json
import BTrees

from substanced.event import subscribe_acl_modified

class EventScribe(object):
    def __init__(self, context):
        self.context = context

    def get_events(self, write=False):
        events = getattr(self.context, '__sd_events__', None)
        if events is None:
            events = BTrees.family64.OO.BTree()
            if write:
                self.context.__sd_events__ = events
        return events
            
    def add(self, name, **kw):
        t = time.time()
        events = self.get_events(True)
        events[str(t)] = (name, json.dumps(kw))

    def since(self, when):
        events = self.get_events()
        return events.items(when)

@subscribe_acl_modified()
def eventsink(event):
    eventscribe = EventScribe(event.object)
    eventscribe.add('aclchanged')
