from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError
from .config import get_elasticsearch_hosts

URL_CACHE_INDEX = 'url_cache'
URL_DOCUMENT_TYPE = 'url'
URL_MAPPING = {
    'url': {
        'properties': {
            'url': {
                'type': 'string',
                'index': 'not_analyzed'
            },
            'resolved': {
                'type': 'string',
                'index': 'not_analyzed'
            }
        }
    }
}

USER_DOCUMENT_TYPE = 'user'
UNPROCESSED_TWEET_DOCUMENT_TYPE = 'rawtweet'
UNPROCESSED_TWEET_MAPPING = {
  'properties': {
    '_default_': {
      'type': 'string',
      'index': 'no'
    },
    'id': {
      'type': 'string',
      'index': 'not_analyzed'
    }
  }
}

_es_connections = {}
def es(universe):
    """Return Elasticsearch connection for the universe"""
    global _es_connections
    if not universe in _es_connections:
        _es_connections[universe] = Elasticsearch(
            hosts=get_elasticsearch_hosts(universe))
    return _es_connections[universe]

def es_url_cache():
    """Returns Elasticsearch connection to the URL_CACHE_INDEX"""
    global _es_connections
    if not URL_CACHE_INDEX in _es_connections:
        _es_connections[URL_CACHE_INDEX] = Elasticsearch()
    return _es_connections[URL_CACHE_INDEX]

def build_universe_mappings(universe):
    es(universe).indices.put_mapping(UNPROCESSED_TWEET_DOCUMENT_TYPE,
        UNPROCESSED_TWEET_MAPPING)

def build_url_cache_mappings():
    es_url_cache().indices.put_mapping(URL_DOCUMENT_TYPE,
        URL_MAPPING,
        index=URL_CACHE_INDEX)


def index_user(universe, user):
    """Add a user to the universe index."""
    es(universe).index(index=universe,
        doc_type=USER_DOCUMENT_TYPE,
        id=user['id'],
        body=user) 

def update_user(universe, user):
    """Update a user in the universe index."""
    es(universe).update(index=universe, doc_type=USER_DOCUMENT_TYPE, id=user['id'],
        body={'doc': user})

def get_universe_users(universe, size=5000):
    """Get users for the universe."""
    res = es(universe).search(index=universe, doc_type=USER_DOCUMENT_TYPE,
        body={}, size=size)
    return res['hits']['hits']

def get_user(universe, user):
    """Get a user from the universe index."""
    return es(universe).get_source(index=universe, doc_type=USER_DOCUMENT_TYPE, id=user['id'])

def save_user(universe, user):
    """Check if a user exists in the database. If not, create it. Otherwise, If so, update it if need be."""
    try:
        old_user = get_user(universe, user)
    except NotFoundError:
        # Add the new user to the index
        index_user(universe, user)
    else:
        if len(user.keys()) == 1 and len(old_user.keys()) > 1:
            # We already have user metadata, don't update.
            pass
        else:
            update_user(universe, user)

def enqueue_tweet(universe, tweet):
    """Save a tweet to the universe index as an uprocessed tweet document."""
    es(universe).index(index=universe,
        doc_type=UNPROCESSED_TWEET_DOCUMENT_TYPE,
        id=tweet['id'],
        body=tweet)

def get_url_cache(url):
    """Get a URL from the URL_CACHE_INDEX"""
    try:
        return es_url_cache().get_source(index=URL_CACHE_INDEX, 
            id=url, doc_type=URL_DOCUMENT_TYPE)
    except NotFoundError:
        return None

def set_url_cache(url, resolved_url):
    """Index a URL and its resolution in Elasticsearch"""
    body = {
        'url': url,
        'resolved': resolved_url
    }
    es_url_cache().index(index=URL_CACHE_INDEX, doc_type=URL_DOCUMENT_TYPE,
        body=body, id=url)
