==========================================
Changing Resource Structure With Evolution
==========================================

As you develop your software and make changes to structures,
your existing content will be in an old state. Whether in production or
during development, you need a facility to correct out-of-date data.

Evolution provides a rich facility for "evolving" your resources to
match changes during development. Substance D's evolution facility
gives Substance D developers full control over the data updating process:

- Write scripts for each package that get called during an update

- Set revision markers in the data to indicate the revision level a
  database is at

- Console script that can be run to "evolve" a database

Running an Evolution
====================

Substance D applications generate a console script at
``bin/sdi_evolve``. Running this without arguments displays some help:

.. code-block:: bash

    $ bin/sd_evolve
    Requires a config_uri as an argument

    sd_evolve [--latest] [--set-db-version=num] [--package=name] config_uri
      Evolves new database with changes from scripts in evolve packages
         - with no arguments, evolve just displays versions
         - with the --latest argument, evolve runs scripts as necessary
         - if --package is specified, only operate against the specified
           package name.
         - with the --set-db-version argument, evolve runs no scripts
           but just sets the database 'version number' for a package
           to an arbitrary integer number.  Requires --package.

    e.g. sd_evolve --latest etc/development.ini

Running with your INI file, as explained in the help,
shows information about the version numbers of various packages:

.. code-block:: bash

    $ bin/sd_evolve etc/development.ini

    Package substanced.evolution
    Code at software version 4
    Database at version 2
    Not evolving (latest not specified)

This shows that we have one package (``substanced``) registered with
evolution and that this database has evolved that package to version 4.

Adding Evolution Support To a Package
=====================================

Let's say we have been developing an ``sdidemo`` package and,
with content already in the database, we want to add evolution support.
Our ``sdidemo`` package is designed to be included into a site,
so we have the traditional Pyramid ``includeme`` support. In there we
add the following:

.. code-block:: python

    def includeme(config):
        config.add_evolution_package('sdidemo.evolution')

We then add a directory ``sdidemo/evolution`` with an ``__init__.py``
containing the following:

.. code-block:: python

    #
    # Evolve scripts for the sdidemo
    #

    VERSION = 1

We need a module to act as an evolve step, so we place the following in
``sdidemo/evolution/evolve1.py``:

.. code-block:: python

    import logging

    logger = logging.getLogger('evolution')

    def evolve(root):
        logger.info(
            'Running sdidemo evolve step 1: say hello'
        )

Running ``sd_evolve`` *without* ``--latest`` (meaning,
without performing an evolution) shows that Substance D's evolution now
knows about our package:

.. code-block:: bash

    $ bin/sd_evolve etc/development.ini

    Package substanced.evolution
    Code at software version 4
    Database at version 2
    Not evolving (latest not specified)

    Package sdidemo.evolution
    Code at software version 4
    Database at version 0
    Not evolving (latest not specified)

Let's now run ``sd_evolve`` "for real" and set a version number in the
database for our ``sdidemo`` package:

.. code-block:: bash

    $ bin/sd_evolve etc/development.ini

    Package substanced.evolution
    Code at software version 4
    Database at version 4
    Evolved substanced.evolution to 4

    Package sdidemo.evolution
    Code at software version 1
    Database at version 1
    Evolved sdidemo.evolution to 1

This examples shows a number of points:

- Each package can easily add evolution support via the
  ``config.add_evolution_package()`` directive

- The package's evolution support sets a version number and then
  defined a series of ``evolveN.py`` evolution modules, where ``N`` is
  a single- or multi-digit integer.

- Substance D's evolution service looks at the database to see the
  at what revision number that package was last run,
  then runs all the needed evolve scripts, sequentially,
  to bring the database up to date

- All changes within an evolve script are in the scope of a
  transaction. If all the evolve scripts run to completion without
  exception, the transaction is committed.

Manually Setting a Revision Number
==================================

In some cases you might have performed the work in an evolve step by
hand and you know there is no need to re-perform that work. But you'd
like to bring the evolution revision number up for that package.

The ``--set-db-version argument`` argument to ``sd_evolve``
accomplishes this, along with the ``--package`` that you would like to
manually set the revision number for.

Baselining
==========

Evolution is baselined at first startup. One of the
problems with generic evolution is that, you might get a package and it
will be at version 7. But there's no initial version in the database.
Substance D, in the root factory, says: "I know all the
packages participating in evolution, so when I first create the root
object, I will set everything to the current package number."

