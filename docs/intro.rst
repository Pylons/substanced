.. _introduction:

Introduction
============

.. sidebar::  A Scanner Darkly

    "The two hemispheres of my brain are competing?" Fred said.

    "Yes."

    "Why?"

    "Substance D. It often causes that, functionally. This is what we
    expected; this is what the tests confirm. Damage having taken place in
    the normally dominant left hemisphere, the right hemisphere is attempting
    to compensate for the impairment. But the twin functions do not fuse,
    because this is an abnormal condition the body isn't prepared for. It
    should never happen. "Cross-cuing", we call it. Related to splitbrain
    phenomena. We could perform a right hemispherectomy, but--"

    "Will this go away," Fred interrupted, "when I get off Substance D?"

    "Probably," the psychologist on the left said, nodding. "It's a
    functional impairment."

    The other man said, "It may be organic damage. It may be
    permanent. Time'll tell, and only after you are off Substance D for a
    long while. And off entirely."

    "What?" Fred said. He did not understand the answer-- was it yes or no?
    Was he damaged forever or not? Which had they said?

        -- Philip K. Dick, A Scanner Darkly


Substance D is an application server.  It provides the following features:

- Facilities that allow developers to define "content" (e.g., "a blog entry",
  "a product", or "a news item").

- A management (a.k.a., "admin") web UI which allows non-expert but privileged
  users to create, edit, update, and delete developer-defined content, as well
  as managing other aspects of the system such as users, groups, security, and
  so on.

- "Undo" capability for actions taken via the management UI.

- A way to make highly granular hierarchical security declarations for content
  objects (e.g., "Bob can edit *this* post" or "Bob can edit all posts in this
  collection" as opposed to just "Bob can edit posts").

- Built-in users and groups management.

- Built-in content workflow.

- Indexing and searching of content (field, keyword, facet, and full-text).
  Searches can be easily filtered by the security settings of individual pieces
  of content, by path in the content hierarchy, or by a combination of the two.

- A facility for relating content objects to each other (with optional
  referential integrity).

- An "evolve" mechanism for evolving content over time as it changes.

- A mechanism to dump your site's content to the filesystem in a mostly
  human-readable format, and a mechanism to reload a dump into the system.

Substance D is built upon the following technologies:

- `ZODB <http://zodb.org>`_

- `Pyramid <http://pylonsproject.org>`_

- `hypatia <https://github.com/Pylons/hypatia>`_

- `colander <http://docs.pylonsproject.org/projects/colander/en/latest/>`_

- `deform <http://docs.pylonsproject.org/projects/deform/en/latest/>`_
