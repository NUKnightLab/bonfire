from elasticsearch import Elasticsearch
from .config import get_elasticsearch_hosts

_es_connections = {}
def es(universe):
    """Return Elasticsearch connection for the universe"""
    global _es_connections
    if not universe in _es_connections:
        _es_connections[universe] = Elasticsearch(
            hosts=get_elasticsearch_hosts(universe))
    return _es_connections[universe]
    

def save_user(universe, user):
    """Save a user to the universe index."""
    es(universe).index(index=universe, doc_type='user', id=user['id'],
        body=user) 


