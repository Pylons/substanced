Building a Retail Application
-----------------------------

It's not the intent that normal unprivileged users of an application you build
using Substance D ever see the :term:`SDI` management interface.  That
interface is reserved for privileged users, like you and your staff.

To build a "retail" application, you just use normal Pyramid :term:`view
configuration` to associate objects with view logic based on the content
types provided to you by Substance D and the content types you've defined.

For example, here's a view that will respond on the root Substance D object
and return its SDI title:

.. code-block:: python
   :linenos:

   from pyramid.view import view_config

   @view_config(content_type='Root')
   def hello(request):
       html = u'<html><head></head><body>Hello from %s!</body></html>'
       request.response.text = html % request.context.sdi_title
       return request.response

Note that we did *not* use the :class:`substanced.sdi.mgmt_view` decorator.
Instead we used the :class:`pyramid.view.view_config` decorator, which will
expose the view to normal site visitors, not just those visiting the
resource via the :term:`SDI`.

To see that code working, create a ``retail`` package within the ``myproj``
package (that is the inner ``myproj`` folder that contains the
``__init__.py``, ``resources.py`` and ``views.py`` files). The package will
have two files: an empty ``__init__.py`` and a ``views.py`` with the code
snippet above. If you now visit ``http://localhost:6543/`` you will see the
"Hello from..." message.

To display actual content stored in the database, Substance D exposes a
:term:`resource tree` that you can hang views from to build your application.
You'll want to read up on :term:`traversal` to understand how to associate
view configuration with :term:`resource` objects.
