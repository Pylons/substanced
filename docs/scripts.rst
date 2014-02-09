Substance D Command-Line Utilities
==================================

Substance D installs a number of helper scripts for performing admin-related
tasks.  To get full command-line syntax for any script, run it with
:option:`--help`.

:program:`sd_adduser`
---------------------

Add a new user, making them part of the 'admins' group.  Useful when
recovering from a forgotten password for the default 'admin' user.  E.g.:

.. code-block:: sh

   $ /path/to/virtualenv/bin/sd_adduser /path/to/virtualenv/etc/production.ini phred password

:program:`sd_drain_indexing`
----------------------------

Process deferred indexing actions.  E.g., run this from a :command:`cron`
job to drain the queue every two minutes:

.. code-block:: guess

  0-59/2 * * * * /path/to/virtualenv/bin/sd_drain_indexing /path/to/virtualenv/etc/production.ini

:program:`sd_dump`
------------------

Dump an object (and its subobjects) to the filesystem.::

    sd_dump [--source=ZODB-PATH] [--dest=FILESYSTEM-PATH] config_uri
    Dumps the object at ZODB-PATH and all of its subobjects to a
    filesystem path.  Such a dump can be loaded (programmatically)
    by using the substanced.dump.load function

E.g.:

.. code-block:: sh

   $ /path/to/virtualenv/bin/sd_dump --source=/ --dest=/tmp/dump /path/to/virtualenv/etc/development.ini

:program:`sd_evolve`
--------------------

Query for pending evolution steps, or run them to get the database
up-to-date.  See :ref:`sd_evolve-narrative`.

:program:`sd_reindex`
---------------------

Reindex the catalog.  E.g.:

.. code-block:: sh

   $ /path/to/virtualenv/bin/sd_reindex /path/to/virtualenv/etc/development.ini
