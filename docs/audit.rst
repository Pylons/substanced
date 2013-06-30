==============
Using Auditing
==============

Substance D keeps an audit log of all meaningful operations performed against
content.  At the time of this writing, "meaningful" is defined as:

- When an ACL is changed.

- When a resource is added or removed.

- When a resource is modified.

The audit log is of a fixed size (currently 10,000 items).  When the audit log
fills up, the oldest audit event is thrown away.  Currently there is no user
interface to view the audit log, and we don't have an archiving mechanism in
place to keep around the items popped off the end of the log when it fills up;
both of these are planned.

You can extend the auditing system by using the
:class:`substanced.audit.AuditScribe`, writing your own events to the log.

Adding an Audit Log Entry
=========================

Here's an example of adding an audit log entry of type ``NailsFiled`` to the
audit log:

.. code-block:: python

   from substanced.audit import AuditScribe
   from substanced.util import get_oid

   def myview(context, request):
       scribe = AuditScribe(context)
       scribe.add('NailsFiled', get_oid(context), type='fingernails')
       ...

This will add a ``NailsFiled`` event with the payload
``{'type':'fingernails'}`` to the audit log.  The payload will also
automatically include a UNIX timestamp as the key ``time``.  The first argument
is the audit log typename.  Audit entries of the same kind should share the
same type name.  It should be a string.  The second argument is the oid of the
content object which this event is related to.  It may be ``None`` indicating
that the event is global, and unrelated to any particular piece of content.
You can pass any number of keyword arguments to
:meth:`substanced.audit.AuditScribe.add`, each will be added to the payload.

Using The ``auditstream-sse`` View
==================================

You can use a view named ``auditstream-sse`` against any resource in your
resource tree using JavaScript.  It will return an event stream suitable for
driving an HTML5 ``EventSource`` (an HTML 5 feature, see
http://www.html5rocks.com/en/tutorials/eventsource/basics/ for more
information).  The event stream will contain auditing events.  This can be used
for progressive enhancement of your application's UI.

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

The executing user will need to possess the ``sdi.view-auditstream`` permission
against the context on which the view is invoked.  Each event payload will
contain detailed information about the audit event as a string which represents
a JSON dictionary.
