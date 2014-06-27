from .db import get_url_cache, set_url_cache
import requests

def increase_connection_pools(session):
    """ Change session defaults for a requests.session object, optimized for many connections at once. """
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
    cached_url = get_url_cache(url)
    if cached_url:
        return cached_url['resolved']

    if session is None:
        session = increase_connection_pools(requests.Session())
    try:
        resolved_url = session.head(url, timeout=4, allow_redirects=True).url
    except:
        resolved_url = url
    set_url_cache(url, resolved_url)
    return resolved_url
