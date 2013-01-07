============================
Gathering Runtime Statistics
============================

Problems can come up in production. When they do, you usually want
forensics that show aspects of the system under load,
over a period of time.

Of course, you don't want the collection of such data to affect
performance. What's needed is a mechanism to log data all the time,
in a lightweight way, that can later be analyzed in productive ways.
This system needs both built-in hooks at the Substance D framework
level as well as extension points to analyze function points in the
application you are writing.

For this, Substance D supports
`DataDog <http://www.datadoghq.com/>`_, a software-as-a-service (SaaS)
provider for monitoring and visualizing performance data. DataDog
installs an agent on your local system. This agent is based on
`statsd <https://github.com/etsy/statsd>`_ which is used in other
systems such as Graphite.

Setting Up Your Site
====================

To enable statistics in your site, edit your ``.ini`` configuration
file and add the following lines to your ``[app:main]`` section::

    substanced.statsd.enabled = true
    substanced.statsd.host = localhost
    substanced.statsd.port = 8125
    substanced.statsd.prefix = substanced

Then, sign up for an account with DataDog. This will provide you with
the instructions for downloading and running the local agent.

Once you log into your DataDog dashboard, click on ``Infrastructure``
and you'll see any hosts configured as part of your account:

.. image:: images/datadog1.png

The ``substanced`` entry in ``Apps`` is from the
``substanced.statsd.prefix`` mentioned above. Clicking on that brings
up Substance D specific monitoring in DataDog:

.. image:: images/datadog2.png

Logging Custom Statistics
=========================

Over time, Substance D itself will include more framework points where
statistics are collected. Most likely, though, you'll want some
statistics that are very meaningful to your application's specific
functionality.

If you look at the docs for the
`Python statsd
module <http://statsd.readthedocs.org/en/v0.5.0/types.html>`_ you will
see three main types:

- *Counters* for simply incrementing a value,

- *Timers* for logging elapsed time in a code block, and

- *Gauges* for tracking a constant at a particular point in time

Each of these map to methods in
:py:class:`substanced.stats.StatsdHelper`. This class is available as
an instance available via import:

.. code-block:: python

    from substanced.stats import statsd_gauge

Your application code can then make calls to these stats-gathering
methods. For example, :py:class:`substanced.principal.User` does the
following to note that check password was used:

.. code-block:: python

    statsd_gauge('check_password', 1)

Here is an example in
:py:meth:`substanced.catalog.Catalog.index_resource` that measures
elapsed indexing time inside a Python ``with`` block:

.. code-block:: python

    with statsd_timer('catalog.index_resource'):
        if oid is None:
            oid = oid_from_resource(resource)
        for index in self.values():
            index.index_resource(resource, oid=oid, action_mode=action_mode)
        self.objectids.insert(oid)
