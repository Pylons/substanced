
import re
import os
import unidecode

from substanced._compat import u
from substanced.sdi import default_sdi_addable

re_word = re.compile(r'\W+')


def slugify_in_context(context, name, remove_extension=True):
    if remove_extension:
        name = os.path.splitext(name)[0]

    slug = unidecode.unidecode(u(name)).lower()
    orig = slug = re_word.sub('-', slug)
    i = 1
    while True:
        if slug not in context:
            break
        slug = '%s-%i' % (orig, i)
        i += 1
    return slug


def content_type_addable(context, request, content_type):
    """Determine whether resources of type ``content_type`` can be added
    to ``context`` using the SDI management interface.

    Returns ``True`` iff resources of the type named by ``content_type`` can be
    added to ``context`` using the SDI management interface.

    Addability is determined by consulting the ``__sdi_addable__``
    attribute of the ``context``.  See
    :ref:`filtering-what-can-be-added` for details.p

    """
    introspector = request.registry.introspector
    discrim = ('sd-content-type', content_type)
    intr = introspector.get('substance d content types', discrim)
    if intr is None:
        return False            # unknown content_type

    sdi_addable = getattr(context, '__sdi_addable__', default_sdi_addable)
    if sdi_addable is None:
        return True
    elif callable(sdi_addable):
        return sdi_addable(context, intr)
    else:
        return content_type in sdi_addable
