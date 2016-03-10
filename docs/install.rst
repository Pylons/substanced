Installation
============

Install using pip, e.g. (within a virtualenv)::

  $ pip substanced

.. warning::

   During Substance D's alpha period, it may be necessary to use a
   checkout of Substance D as well as checkouts of the most recent versions of
   the libraries upon which Substance D depends.

.. _optional_dependencies:

Demonstration Application
-------------------------

See the application running at http://demo.substanced.net for a demonstration
of the Substance D management interface.

You can deploy the demonstration application locally by performing the
following steps.

#. Create a new directory somewhere and ``cd`` to it::

   $ virtualenv -p python2.7 hack-on-substanced
   $ cd hack-on-substanced

#. Install Substance D either from PyPI or from a git checkout::

   $ bin/pip install substanced
   
   OR::
   
   $ bin/pip install git+https://github.com/Pylons/substanced#egg=substanced

   Alternatively create a writeable fork on GitHub and check that out.
   
#. Check that the python-magic library has been installed::

   $ bin/python -c "from substanced.file import magic; assert magic is not None, 'python-magic not installed'"
   
   If you then see "python-magic not installed" then you will need to take
   additional steps to install the python-magic library. See :doc:`magic`.
   
#. Move back to the parent directory::

   $ cd ..

#. Now you should be able to create new Substance D projects by
   using ``pcreate``. The following ``pcreate`` command uses the scaffold
   ``substanced`` to create a new project named ``myproj``::
      
   $ hack-on-substanced/bin/pcreate -s substanced myproj

#. Now you can make a virtualenv for your project and move into it::

   $ virtualenv -p python2.7 myproj
   $ cd myproj

#. Install that project using ``pip install -e`` into the virtualenv::

   $ bin/pip install -e .

#. Run the resulting project via ``bin/pserve development.ini``. The
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
