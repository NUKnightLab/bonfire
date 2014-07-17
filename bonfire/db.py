import time
import datetime
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError
from .config import get_elasticsearch_hosts

MANAGEMENT_INDEX = 'bonfire'
CONTENT_DOCUMENT_TYPE = 'content'
CACHED_URL_DOCUMENT_TYPE = 'url'
CACHED_URL_MAPPING = {
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

USER_DOCUMENT_TYPE = 'user'
TWEET_DOCUMENT_TYPE = 'tweet'
TWEET_MAPPING = {
    'properties': {
        'content_url': {
            'type': 'string',
            'index': 'not_analyzed'
        },
        'created': {
            'type': 'date',
            'format': 'EE MMM d HH:mm:ss Z yyyy'
        }
    }
}
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


def es_management():
    """Returns Elasticsearch connection to the management index."""
    global _es_connections
    if not MANAGEMENT_INDEX in _es_connections:
        _es_connections[MANAGEMENT_INDEX] = Elasticsearch(
            hosts=get_elasticsearch_hosts())
    return _es_connections[MANAGEMENT_INDEX]


def build_universe_mappings(universe):
    try:
        es(universe).indices.put_mapping(TWEET_DOCUMENT_TYPE,
            TWEET_MAPPING)
        es(universe).indices.put_mapping(UNPROCESSED_TWEET_DOCUMENT_TYPE,
            UNPROCESSED_TWEET_MAPPING)
    except NotFoundError:
        create_index(universe)
        build_universe_mappings(universe)


def build_management_mappings():
    try:
        es_management().indices.put_mapping(CACHED_URL_DOCUMENT_TYPE,
            CACHED_URL_MAPPING,
            index=MANAGEMENT_INDEX)
    except NotFoundError:
        es_management().indices.create(index=MANAGEMENT_INDEX)
        build_management_mappings()


def create_index(universe):
    es(universe).indices.create(index=universe)


def index_user(universe, user):
    """Add a user to the universe index."""
    es(universe).index(index=universe,
        doc_type=USER_DOCUMENT_TYPE,
        id=user['id'],
        body=user) 


def update_user(universe, user):
    """Update a user in the universe index."""
    es(universe).update(index=universe, doc_type=USER_DOCUMENT_TYPE,
        id=user['id'], body={'doc': user})


def get_universe_users(universe, size=5000):
    """Get users for the universe."""
    res = es(universe).search(index=universe, doc_type=USER_DOCUMENT_TYPE,
        body={}, size=size)
    return res['hits']['hits']


def get_user(universe, user):
    """Get a user from the universe index."""
    return es(universe).get_source(index=universe,
        doc_type=USER_DOCUMENT_TYPE, id=user['id'])

def save_user(universe, user):
    """Check if a user exists in the database. If not, create it.
    Otherwise, If so, update it if need be."""
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
    """Save a tweet to the universe index as an unprocessed tweet document.
    """
    es(universe).index(index=universe,
        doc_type=UNPROCESSED_TWEET_DOCUMENT_TYPE,
        id=tweet['id'],
        body=tweet)


def next_unprocessed_tweet(universe):
    """Get the next unprocessed tweet and delete it from the index."""
    # TODO: redo this so it is an efficient queue. Currently for
    # testing only.
    try:
        result = es(universe).search(index=universe,
            doc_type=UNPROCESSED_TWEET_DOCUMENT_TYPE,
            size=1)['hits']['hits'][0]
    except IndexError:
        return None
    try:
        es(universe).delete(index=universe,
            doc_type=UNPROCESSED_TWEET_DOCUMENT_TYPE,
            id=result['_id'])
    except NotFoundError:
        # Something's wrong. Ignore it for now.
        return next_unprocessed_tweet(universe)
    return result


def save_tweet(universe, tweet):
    """Save a tweet to the universe index, fully processed."""
    es(universe).index(index=universe,
        doc_type=TWEET_DOCUMENT_TYPE,
        id=tweet['id'],
        body=tweet)


def save_content(content):
    """Save the content of a URL to the management index."""
    es_management().index(index=MANAGEMENT_INDEX,
        doc_type=CONTENT_DOCUMENT_TYPE,
        id=content['url'],
        body=content)


def get_cached_url(url):
    """Get a resolved URL from the management index. Returns None if URL doesn't
    exist."""
    try:
        return es_management().get_source(index=MANAGEMENT_INDEX, 
            id=url.rstrip('/'), doc_type=CACHED_URL_DOCUMENT_TYPE)['resolved']
    except NotFoundError:
        return None


def set_cached_url(url, resolved_url):
    """Index a URL and its resolution in Elasticsearch"""
    body = {
        'url': url.rstrip('/'),
        'resolved': resolved_url.rstrip('/')
    }
    es_management().index(index=MANAGEMENT_INDEX,
        doc_type=CACHED_URL_DOCUMENT_TYPE, body=body, id=url)


def get_universe_tweets(universe, query=None, since=24, size=100):
    """Gets all tweets in a given universe.
    If query is None, fetches all.
    If query is a string, fetches tweets matching the string's text.
    If query is a dict, uses Elasticsearch Query DSL to parse it
    (http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/query-dsl.html)."""
    if query is None:
        body = {
            'query': {
                'match_all': {}
            }
        }
    elif isinstance(query, basestring):
        body = {
            'query': {
                'match': {
                    'text': query
                }
            }
        }
    else:
        body = {
            'query': {
                'match': query
            }
        }
    body['filter'] = {
        'range': {
            'created': {
                'gte': 'now-%dh' % since,
                'lte': 'now'
            }
        }
    }
    res = es(universe).search(index=universe, doc_type=TWEET_DOCUMENT_TYPE,
        body=body, size=size)
    return [tweet['_source'] for tweet in res['hits']['hits']]

def search_content(query, size=100):
    """Search fulltext of all content for a given string, 
    or a custom match query."""
    if isinstance(query, basestring):
        query = {'text': query}
    body = {
        'query': {
            'match': query
        }
    }
    res = es_management().search(index=MANAGEMENT_INDEX, doc_type=CONTENT_DOCUMENT_TYPE,
        body=body, size=size)
    return [content['_source'] for content in res['hits']['hits']]

def get_popular_content(universe, since=24, size=100):
    """Gets the most popular URLs shared from a given universe,
    and returns their full content.
    """
    body = {
        'aggregations': {
            'recent_tweets': {
                'filter': {
                    'range': {
                        'created': {
                            'gte': 'now-%dh' % since,
                            'lte': 'now'
                        }
                    }
                },
                'aggregations': {
                    CONTENT_DOCUMENT_TYPE: {
                        'terms': {
                            'field': 'content_url',
                            'size': size
                        },
                        'aggregations': {
                            'first_tweeted': {
                                'min': {
                                    'field': 'created'
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    res = es(universe).search(index=universe, doc_type=TWEET_DOCUMENT_TYPE,
        body=body, size=0)
    top_urls = dict([(url['key'], url['first_tweeted']['value']) for url in
        res['aggregations']['recent_tweets'][CONTENT_DOCUMENT_TYPE]['buckets']])
    if not top_urls:
        return top_urls.keys()

    # Now query the content index to get the full metadata for these urls.
    content_res = es_management().mget({'ids': top_urls.keys()}, 
        index=MANAGEMENT_INDEX, doc_type=CONTENT_DOCUMENT_TYPE)

    top_content = []
    for content in content_res['docs']:
        if not content['found']:
            continue
        first_tweeted = top_urls[content['_source']['url']]
        content['_source']['first_tweeted'] = format_time(first_tweeted)
        top_content.append(content['_source'])
    return top_content

def format_time(epoch):
    now = datetime.datetime.utcnow()
    then = datetime.datetime(*time.gmtime(epoch / 1000)[:7])
    diff = now - then
    days = diff.days
    if days > 1:
        return '%d days' % days
    elif diff.days == 1:
        return '%d day' % days
    second_diff = (now - then).seconds
    hours = second_diff / 60 / 60
    if hours > 1:
        return '%d hours' % hours
    elif hours == 1:
        return '%d hour' % hours
    minutes = second_diff / 60
    if minutes > 1:
        return '%d minutes' % minutes
    elif minutes == 1:
        return '%d minute' % minutes
    else:
        return '%d seconds' % second_diff
