from substanced.event import subscribe_acl_modified

from . import EventScribe

@subscribe_acl_modified()
def eventsink(event):
    eventscribe = EventScribe(event.object)
    eventscribe.add('aclchanged')
