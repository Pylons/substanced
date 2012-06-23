=================================
Step 05: Adding a Management View
=================================



Objectives
==========

- Publish static assets from a custom directory

- Filling the head slot to load extra resources

- Provide a new folder tab that lists Documents in a table



Analysis
========

- Used ``config.add_static_view`` to add ``tut_static`` to the URL space

- Used ``request.static_url`` in the template to make a full URL

- We made a new ``@mgmt_view`` that is registered against anything that
  supports ``IFolder`` (whether built-in container types or custom)

- The view filtered out ``context.values`` which don't have a ``title``