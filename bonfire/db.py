import time
import datetime
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError, TransportError
from .config import get_elasticsearch_hosts

MANAGEMENT_INDEX = 'bonfire'
CONTENT_DOCUMENT_TYPE = 'content'
CONTENT_MAPPING = {
    'properties': {
        'url': {
            'type': 'string',
            'index': 'not_analyzed'
        }
    }
}
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
            'format': 'EEE MMM d HH:mm:ss Z yyyy'
        },
        'id_str': {
            'type': 'string',
            'index': 'not_analyzed'
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
        es_management().indices.put_mapping(CONTENT_DOCUMENT_TYPE,
            CONTENT_MAPPING,
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


def get_universe_tweets(universe, query=None, start=None, end=None, size=100):
    """Gets all tweets in a given universe.
    If query is None, fetches all.
    If query is a string, fetches tweets matching the string's text.
    If query is a dict, uses Elasticsearch Query DSL to parse it
    (http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/query-dsl.html)."""
    if not end:
        end = datetime.datetime.utcnow()
    if start is None:
        start = 24
    if isinstance(start, int):
        start = end - datetime.timedelta(hours=start)

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
                'gte': format_date(start),
                'lte': format_date(end)
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

def search_universe_content(universe, term, start=None, end=None, size=100):
    """Searches tweet text and content text for term matches in a given universe.
    """
    # Search for a) tweets matching the given term, and b) all content URLs in the given time frame
    if not end:
        end = datetime.datetime.utcnow()
    if start is None:
        start = 24
    if isinstance(start, int):
        start = end - datetime.timedelta(hours=start)

    body = {
        'filter': {
            'and': [{
                'term': {
                    'text': term
                    }
                }, {
                'range': {
                    'created': {
                        'gte': format_date(start),
                        'lte': format_date(end)
                        }
                    }
                }
            ]
        },
        'aggregations': {
            'recent_tweets': {
                'filter': {
                    'range': {
                        'created': {
                            'gte': format_date(start),
                            'lte': format_date(end)
                        }
                    }
                },
                'aggregations': {
                    CONTENT_DOCUMENT_TYPE: {
                        'terms': {
                            'field': 'content_url',
                            'size': size * 10
                        },
                        'aggregations': {
                            'first_tweeted': {
                                'min': {
                                    'field': 'created'
                                }
                            },
                            'tweeters': {
                                'terms': {
                                    'field': 'user_screen_name'
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    try:
        res = es(universe).search(index=universe, doc_type=TWEET_DOCUMENT_TYPE, body=body, size=size)
    except TransportError:
        sorted_urls = []
        first_tweeted_map = {}
        tweet_urls = set()
        matching_urls = set()
    else:
        aggs = res['aggregations']['recent_tweets'][CONTENT_DOCUMENT_TYPE]['buckets']
        sorted_res = sorted(aggs, key=lambda r: len(r['tweeters']['buckets']), reverse=True)
        sorted_urls = [u['key'] for u in sorted_res]
        first_tweeted_map = dict([(url['key'], url['first_tweeted']['value']) for url in sorted_res])
        tweet_urls = set([u['key'] for u in aggs])
        matching_urls = set([u['_source']['content_url'] for u in
            res['hits']['hits']])


    # Now search content database and get all the urls with this term
    body = {
        'query': {
            'match': {
                'text': term,
            }
        },
        'aggregations': {
            'urls': {
                'terms': {
                    'field': 'url',
                    'size': size * 10
                }
            }
        }
    }
    res = es_management().search(index=MANAGEMENT_INDEX, doc_type=CONTENT_DOCUMENT_TYPE,
        body=body, size=0)
    content_urls = set([u['key'] for u in res['aggregations']['urls']['buckets']])

    # Find just the ones within the time frame, then include the ones that matched the tweet text
    all_urls = (content_urls & tweet_urls) | matching_urls
    if not all_urls:
        return []

    # Finally, query the content to get the top 20 links from here
    content_res = es_management().mget({'ids': list(all_urls)}, 
        index=MANAGEMENT_INDEX, doc_type=CONTENT_DOCUMENT_TYPE)

    def sort_index(item):
        try:
            return sorted_urls.index(item)
        except ValueError:
            return -1

    top_content = []
    content = sorted(filter(lambda c: c['found'], 
        content_res['docs']), key=lambda x: sort_index(x['_source']['url']), reverse=True)
    for index, item in enumerate(content):
        source = item['_source']
        try:
            first_tweeted = first_tweeted_map[source['url']]
        except KeyError:
            first_tweeted = 0
        source['first_tweeted'] = format_time(first_tweeted)
        source['rank'] = index + 1
        top_content.append(source)
    return top_content
    

def get_popular_content(universe, start=None, end=None, size=100):
    """Gets the most popular URLs shared from a given universe,
    and returns their full content.
    """
    if not end:
        end = datetime.datetime.utcnow()
    if start is None:
        start = 24
    if isinstance(start, int):
        start = end - datetime.timedelta(hours=start)
    body = {
        'aggregations': {
            'recent_tweets': {
                'filter': {
                    'range': {
                        'created': {
                            'gte': format_date(start),
                            'lte': format_date(end)
                        }
                    }
                },
                'aggregations': {
                    CONTENT_DOCUMENT_TYPE: {
                        'terms': {
                            'field': 'content_url',
                            'size': size * 5,
                            'min_doc_count': 2
                        },
                        'aggregations': {
                            'first_tweeted': {
                                'min': {
                                    'field': 'created'
                                }
                            },
                            'tweeters': {
                                'terms': {
                                    'field': 'user_screen_name'
                                }
                            },
                            'tweet_ids': {
                                'terms': {
                                    'field': 'id_str',
                                    'size': 1
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    res = es(universe).search(index=universe, doc_type=TWEET_DOCUMENT_TYPE,
        body=body, size=0)['aggregations']['recent_tweets'][CONTENT_DOCUMENT_TYPE]['buckets']

    res = sorted(res, key=lambda r: len(r['tweeters']['buckets']), reverse=True)[:size]
    top_urls = [url['key'] for url in res]
    if not top_urls:
        return top_urls
    first_tweeted_map = dict([(url['key'], url['first_tweeted']['value']) for url in res])
    tweet_ids = [url['tweet_ids']['buckets'][0]['key'] for url in res]

    # Now query the content index to get the full metadata for these urls.
    content_res = es_management().mget({'ids': top_urls}, 
        index=MANAGEMENT_INDEX, doc_type=CONTENT_DOCUMENT_TYPE)

    # Finally, get tweets related to these urls
    tweet_res = es(universe).mget({'ids': tweet_ids},
        index=universe, doc_type=TWEET_DOCUMENT_TYPE)['docs']
    
    top_content = []
    content = filter(lambda c: c['found'], content_res['docs'])
    for index, item in enumerate(content):
        source = item['_source']
        first_tweeted = first_tweeted_map[source['url']]
        source['first_tweeted'] = format_time(first_tweeted)
        try:
            tweet = filter(lambda t: t['_source']['content_url'] == source['url'], tweet_res)[0]
        except IndexError:
            source['tweet'] = {}
        else:
            source['tweet'] = {
                'user_screen_name': tweet['_source']['user_screen_name'],
                'text': tweet['_source']['text'],
                'user_profile_image_url': tweet['_source']['user_profile_image_url']
            }
        source['rank'] = index + 1
        top_content.append(source)
    return top_content

def format_date(dt):
    return dt.strftime('%a %b %d %H:%M:%S +0000 %Y')

def pluralize(word, amt):
    resp = "%d %s" % (amt, word)
    if amt > 1:
        return resp + "s"
    elif amt == 1:
        return resp
    return None

def format_time(epoch):
    then = datetime.datetime(*time.gmtime(epoch / 1000)[:7])
    diff = datetime.datetime.utcnow() - then
    time_map = (
        ('day', diff.days),
        ('hour', diff.seconds / 60 / 60),
        ('minute', diff.seconds / 60),
        ('second', diff.seconds)
    )
    for word, amt in time_map:
        if pluralize(word, amt):
            return pluralize(word, amt)
    return 'just now'
