import time
import json

import persistent
import BTrees
import BTrees.Length

EVENTS_ATTR = '__sd_events__'

class Events(persistent.Persistent):
    def __init__(self, max_items):
        self.max_items = max_items
        self.events = BTrees.family64.OO.BTree()
        self.length = BTrees.Length.Length()

    def add(self, name, **kw):
        t = time.time()
        events = self.events
        length = self.length
        while length > self.max_items:
            try:
                minkey = events.minKey()
            except ValueError:
                # might as well mess with this thing, it's out of sync, although
                # it should never be
                length.set(0)
                break
            del events[minkey]
            length.change(-1)
        events[str(t)] = (name, json.dumps(kw))
        length.change(1)

    def since(self, when):
        return self.events.items(when)
        
        
class EventScribe(object):
    def __init__(self, context, max_items=100):
        self.context = context
        self.max_items = max_items

    def get_events(self):
        return getattr(self.context, EVENTS_ATTR, None)

    def add(self, name, **kw):
        events = self.get_events()
        if events is None:
            events = Events(self.max_items)
            setattr(self.context, EVENTS_ATTR, events)
        events.add(name, **kw)
            
    def since(self, when):
        events = self.get_events()
        if events is None:
            return []
        return events.since(when)

