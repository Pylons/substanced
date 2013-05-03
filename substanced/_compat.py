try:
    STRING_TYPES = (str, unicode)
except NameError: #pragma NO COVER Python >= 3.0
    STRING_TYPES = (str,)

try:
    u = unicode
except NameError: #pragma NO COVER Python >= 3.0
    def u(x, encoding='ascii'):
        if isinstance(x, str):
            return x
        if isinstance(x, bytes):
            return x.decode(encoding)
    b = bytes
else: #pragma NO COVER Python < 3.0
    b = str

try:
    long
except NameError: #pragma NO COVER Python >= 3.0
    INT_TYPES = (int,)
else:
    INT_TYPES = (int, long)

try:
    from urllib.parse import parse_qsl
except ImportError: #pragma NO COVER
    from cgi import parse_qsl

try:
    from urllib.parse import urlsplit
    from urllib.parse import urlunsplit
except ImportError: #pragma NO COVER
    from urlparse import urlsplit
    from urlparse import urlunsplit
