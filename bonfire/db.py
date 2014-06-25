from elasticsearch import Elasticsearch
from .config import get_elasticsearch_hosts

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


def build_universe_mappings(universe):
    es(universe).indices.put_mapping(UNPROCESSED_TWEET_DOCUMENT_TYPE,
        UNPROCESSED_TWEET_MAPPING)

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
    return es(universe).get(index=universe, doc_type=USER_DOCUMENT_TYPE, id=user['id'])

def user_exists(universe, user):
    """Check if a user exists in the universe index."""
    return es(universe).exists(index=universe, doc_type=USER_DOCUMENT_TYPE, id=user['id'])

def save_user(universe, user):
    """Check if a user exists in the database. If not, create it. Otherwise, If so, update it if need be."""
    if user_exists(universe, user):
        old_user = get_user(universe, user)
        if len(user.keys()) == 1 and len(old_user['_source'].keys()) > 1:
            # We already have user metadata, don't update.
            pass
        else:
            update_user(universe, user)
    else:
        index_user(universe, user)

def enqueue_tweet(universe, tweet):
    """Save a tweet to the universe index as an uprocessed tweet document."""
    es(universe).index(index=universe,
        doc_type=UNPROCESSED_TWEET_DOCUMENT_TYPE,
        id=tweet['id'],
        body=tweet)