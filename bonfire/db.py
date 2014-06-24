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
    

def save_user(universe, user):
    """Save a user to the universe index."""
    es(universe).index(index=universe,
        doc_type=USER_DOCUMENT_TYPE,
        id=user['id'],
        body=user) 


def enqueue_tweet(universe, tweet):
    """Save a tweet to the universe index as an uprocessed tweet document."""
    es(universe).index(index=universe,
        doc_type=UNPROCESSED_TWEET_DOCUMENT_TYPE,
        id=tweet['id'],
        body=tweet)
