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
