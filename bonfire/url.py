from .db import get_cached_url, set_cached_url
import requests

def start_session():
    """Start a requests session optimized for many connections at once."""
    session = requests.Session()
    session.max_redirects = 3
    http_adapter = requests.adapters.HTTPAdapter()
    https_adapter = requests.adapters.HTTPAdapter()
    http_adapter.pool_connections = 20
    http_adapter.pool_maxsize = 20
    http_adapter.max_retries = 1
    https_adapter.pool_connections = 20
    https_adapter.pool_maxsize = 20
    https_adapter.max_retries = 1
    session.mount('http://', http_adapter)
    session.mount('https://', https_adapter)
    return session

def resolve_url(url, session=None):
    """ Returns the final destinations of the given urls, allowing redirects """
    cached_url = get_cached_url(url)
    if cached_url:
        return cached_url['resolved']

    if session is None:
        session = start_session()
    try:
        resolved_url = session.head(url, timeout=4, allow_redirects=True).url
    except:
        resolved_url = url
    set_cached_url(url, resolved_url)
    return results
