Installation
============

Install using setuptools, e.g. (within a virtualenv)::

  $ easy_install substanced

.. warning::

   During Substance D's pre-alpha period, it may be necessary to use a
   checkout of Substance D as well as checkouts of the most recent versions of
   the libraries upon which Substance D depends.

.. _optional_dependencies:

Optional Dependencies
---------------------

Use of the :py:attr:`substanced.file.USE_MAGIC` constant for guessing file
types from stream content requires the ``python-magic`` library, which works
without extra help on Linux systems, but requires special dependency
installations on Mac OS and Windows systems.  You'll need to follow these
steps on those platforms to use this feature:

Mac OS X

  http://www.brambraakman.com/blog/comments/installing_libmagic_in_mac_os_x_for_python-magic/

Windows

  "Installation on Win32" in https://github.com/ahupp/python-magic

Demonstration Application
-------------------------

See the application running at http://demo.substanced.net for a demonstration
of the Substance D management interface.

You can deploy the demonstration application locally by performing the
following steps.

#. Create a new directory somewhere and ``cd`` to it::

   $ mkdir ~/hack-on-substanced
   $ cd ~/hack-on-substanced

#. Check out a read-only copy of the Substance D source::

   $ git clone git://github.com/Pylons/substanced.git

   Alternatively create a writeable fork on GitHub and check that out.

#. Create a virtualenv in which to install Substance D::

   $ virtualenv -p python2.7 --no-site-packages env

#. Install ``setuptools-git`` into the virtualenv (for good measure, as we're
   using git to do version control)::

   $ env/bin/easy_install setuptools-git

#. Install Substance D from the checkout into the virtualenv using ``setup.py
   dev``. ``setup.py dev`` is an alias for "setup.py develop" which also
   installs testing requirements such as nose and coverage. Running
   ``setup.py dev`` *must* be done while the current working directory is the
   ``substanced`` checkout directory::

   $ cd substanced
   $ ../env/bin/python setup.py dev

#. At that point, you should be able to create new Substance D projects by
   using ``pcreate``. The following ``pcreate`` command uses the scaffold
   ``substanced`` to create a new project named ``myproj`` in the current
   directory::

   $ cd ../env
   $ bin/pcreate -s substanced myproj

#. Install that project using ``setup.py develop`` into the virtualenv::

   $ cd myproj
   $ ../bin/python setup.py develop

#. Run the resulting project via ``../bin/pserve development.ini``. The
   development server listens to requests sent to http://0.0.0.0:6543 by
   default. Open this URL in a web browser.
   
#. The initial Administrator password is randomly generated automatically.
   Use the following command to find the login information::
   
    $ grep initial_password *.ini
    development.ini:substanced.initial_password = hNyrGI5nnl
    production.ini:substanced.initial_password = hNyrGI5nnl

Hacking on Substance D
----------------------

See `Hacking on Substance D
<https://github.com/Pylons/substanced/blob/master/HACKING.txt>`_, or look in
your checked out local git repository for ``HACKING.txt``, for information and
guidelines to develop your application, including testing and
internationalization. For convenience ``HACKING.txt`` is included below, but
note that lines 6-54 are redundant to the previous section.

.. literalinclude:: ../HACKING.txt
   :language: rst
   :linenos:
   :emphasize-lines: 6-54
