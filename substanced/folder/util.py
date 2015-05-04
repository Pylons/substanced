
import re
import os
import unidecode

from substanced._compat import u

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
