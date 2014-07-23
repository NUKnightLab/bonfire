import time
import datetime
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError, TransportError
from .config import get_elasticsearch_hosts


MANAGEMENT_INDEX = 'bonfire'

# Management index mappings
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

# Universe index mappings
USER_DOCUMENT_TYPE = 'user'
USER_MAPPING = {
    'properties': {
        'id': {
            'type': 'string',
            'index': 'not_analyzed'
        },
        'weight': {
            'type': 'float',
        }
    }
}

TWEET_DOCUMENT_TYPE = 'tweet'
TWEET_MAPPING = {
    'properties': {
        'id': {
            'type': 'string',
            'index': 'not_analyzed'
        },
        'content_url': {
            'type': 'string',
            'index': 'not_analyzed'
        },
        'created': {
            'type': 'date',
            'format': 'EEE MMM d HH:mm:ss Z yyyy'
        },
        'provider': {
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
    """Return Elasticsearch connection for the management index."""
    global _es_connections
    if not MANAGEMENT_INDEX in _es_connections:
        _es_connections[MANAGEMENT_INDEX] = Elasticsearch(
            hosts=get_elasticsearch_hosts())
    return _es_connections[MANAGEMENT_INDEX]


def build_universe_mappings(universe):
    """Create and map the universe index."""
    if not es(universe).indices.exists(universe):
        es(universe).indices.create(index=universe)
    es(universe).indices.put_mapping(USER_DOCUMENT_TYPE,
        USER_MAPPING)
    es(universe).indices.put_mapping(TWEET_DOCUMENT_TYPE,
        TWEET_MAPPING)
    es(universe).indices.put_mapping(UNPROCESSED_TWEET_DOCUMENT_TYPE,
        UNPROCESSED_TWEET_MAPPING)


def build_management_mappings():
    """Create and map the management index."""
    if not es_management().indices.exists(MANAGEMENT_INDEX):
        es_management().indices.create(index=MANAGEMENT_INDEX)
    es_management().indices.put_mapping(CACHED_URL_DOCUMENT_TYPE,
        CACHED_URL_MAPPING,
        index=MANAGEMENT_INDEX)
    es_management().indices.put_mapping(CONTENT_DOCUMENT_TYPE,
        CONTENT_MAPPING,
        index=MANAGEMENT_INDEX)


def get_cached_url(url):
    """Get a resolved URL from the management index.
    Returns None if URL doesn't exist."""
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


def save_content(content):
    """Save the content of a URL to the management index."""
    es_management().index(index=MANAGEMENT_INDEX,
        doc_type=CONTENT_DOCUMENT_TYPE,
        id=content['url'],
        body=content)


def user_exists(universe, user):
    return es(universe).exists(index=universe,
        id=user['id'], doc_type=USER_DOCUMENT_TYPE)


def index_user(universe, user):
    """Add a user to the universe index."""
    user_id = user.get('id_str') or user['id']
    es(universe).index(index=universe,
        doc_type=USER_DOCUMENT_TYPE,
        id=user_id,
        body=user) 


def update_user(universe, user):
    """Update a user in the universe index."""
    es(universe).update(index=universe,
        doc_type=USER_DOCUMENT_TYPE,
        id=user['id'], body={'doc': user})


def save_user(universe, user):
    """Check if a user exists in the database. If not, create it.
    Otherwise, If so, update it if need be."""
    if user_exists(universe, user):
        update_user(universe, user)
    else:
        index_user(universe, user)


def get_universe_users(universe, size=5000):
    """Get users for the universe."""
    res = es(universe).search(index=universe, doc_type=USER_DOCUMENT_TYPE,
        body={}, size=size)
    return res['hits']['hits']


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
        # There are no unprocessed tweets in the universe
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


def get_universe_tweets(universe, query=None, start=24, end=None, size=100):
    """
    Get tweets in a given universe.

    :arg query: accepts None, string, or dict. 
        if None, matches all
        if string, searches across the tweets' text for the given string
        if dict, accepts any elasticsearch match query 
        `<http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/query-dsl-match-query.html>`_
    :arg start: accepts int or datetime (timezone-unaware, UTC)
        if int, starts at that many number of hours before now
    :arg end: accepts datetime (timezone-unaware, UTC), defaults to now.
    :arg size: number of tweets to return
    """

    if not end:
        end = datetime.datetime.utcnow()
    if isinstance(start, int):
        start = end - datetime.timedelta(hours=start)

    # Build query based on what was in the input
    if query is None:
        body = {'query': {'match_all': {}}}
    elif isinstance(query, basestring):
        body = {'query': {'match': {'text': query}}}
    else:
        body = {'query': {'match': query}}

    # Now add date range filter
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
    """
    Search fulltext of all content across universes for a given string, 
    or a custom match query.

    :arg query: accepts a string or dict
        if string, searches fulltext of all content
        if dict, accepts any elasticsearch match query
        `<http://www.elasticsearch.org/guide/en/elasticsearch/reference/current/query-dsl-match-query.html>`_
    :arg size: number of links to return
    """

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


def search_universe_content(universe, term, start=24, end=None, size=100):
    """
    Search the text of both tweets and content for a given term and universe,
    and return some links matching one or the other.

    NOTE: For now, this does not return links in a meaningful order.
    It also does not analyze/tokenize the tweets' text, only the content.

    :arg term: search term to use for querying both tweets and content
    :arg start: accepts int or datetime (timezone-unaware, UTC)
        if int, starts at that many number of hours before now
    :arg end: accepts datetime (timezone-unaware, UTC), defaults to now.
    :arg size: number of links to return
    """

    if not end:
        end = datetime.datetime.utcnow()
    if isinstance(start, int):
        start = end - datetime.timedelta(hours=start)

    # First kill two birds with one stone: search for
    #   a) tweets matching the given term, 
    #   b) all content_urls tweeted from the given universe and time frame,
    #      in the given time frame, along with metadata.
    # It may be better to split this up down the line
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
                                    'field': 'user_screen_name',
                                    'size': 1000
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    try:
        res = es(universe).search(index=universe,
            doc_type=TWEET_DOCUMENT_TYPE, body=body, size=size)
    except TransportError:
        # No results in this queryset
        sorted_urls = []
        first_tweeted_map = {}
        tweet_urls = set()
        matching_urls = set()
    else:
        aggs = res['aggregations']['recent_tweets'][CONTENT_DOCUMENT_TYPE]['buckets']

        # The response sorts by total number of tweets, but we the want number of unique people
        sorted_res = sorted(aggs, 
            key=lambda r: len(r['tweeters']['buckets']), 
            reverse=True)
        sorted_urls = [u['key'] for u in sorted_res]

        first_tweeted_map = dict([(url['key'], 
            url['first_tweeted']['value']) for url in sorted_res])

        # Get a set of all the urls in this time frame...
        tweet_urls = set([u['key'] for u in aggs])
        # ...and of the text-matching urls in this time frame
        matching_urls = set([u['_source']['content_url'] for u in
            res['hits']['hits']])

    # Now search the content database and get all the urls with this term
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
    # Get a set of all the matching urls
    content_urls = set([u['key'] for u in res['aggregations']['urls']['buckets']])

    # Find just the urls within the time frame, 
    # then include the ones that matched the tweet text
    all_urls = (content_urls & tweet_urls) | matching_urls
    if not all_urls:
        return []

    # Finally, query the content to get the top links from here
    content_res = es_management().mget({'ids': list(all_urls)}, 
        index=MANAGEMENT_INDEX, doc_type=CONTENT_DOCUMENT_TYPE)
    matching_content = filter(lambda c: c['found'], content_res['docs'])
    
    # Sort the content by how many tweets it got, which we saved earlier
    # NOTE: this won't grab any of the tweet text matching urls, so put those at the end.
    def sort_index(item):
        try:
            return sorted_urls.index(item)
        except ValueError:
            return -1
    sorted_content = sorted(matching_content,
        key=lambda x: sort_index(x['_source']['url']), reverse=True)[:size]

    # Add some metadata: rank, and when it was first tweeted
    top_content = []
    for index, item in enumerate(sorted_content):
        source = item['_source']
        try:
            first_tweeted = first_tweeted_map[source['url']]
        except KeyError:
            first_tweeted = 0
        source['first_tweeted'] = get_time_since_now(first_tweeted)
        source['rank'] = index + 1
        top_content.append(source)
    return top_content
    

def get_popular_content(universe, start=24, end=None, size=100):
    """
    The default function: gets the most popular links shared 
    from a given universe and time frame.

    :arg start: accepts int or datetime (timezone-unaware, UTC)
        if int, starts at that many number of hours before now
    :arg end: accepts datetime (timezone-unaware, UTC), defaults to now.
    :arg size: number of links to return
    """

    if not end:
        end = datetime.datetime.utcnow()
    if isinstance(start, int):
        start = end - datetime.timedelta(hours=start)

    # Get the top links in the given time frame, and some extra agg metadata
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
                                    'field': 'user_screen_name',
                                    'size': 1000
                                }
                            },
                            'tweet_ids': {
                                'terms': {
                                    'field': 'id',
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
        body=body, size=0)
    res = res['aggregations']['recent_tweets'][CONTENT_DOCUMENT_TYPE]['buckets']
    if not res:
        # There's no content in the given time frame
        return []

    # Save for future reference
    first_tweeted_map = dict([(url['key'], 
        url['first_tweeted']['value']) for url in res])

    # The response sorts by total number of tweets, but we the want number of unique people
    res = sorted(res, 
        key=lambda r: (len(r['tweeters']['buckets'])), reverse=True)[:size]

    # Query the content index to get the full metadata for these urls.
    top_urls = [url['key'] for url in res]
    content_res = es_management().mget({'ids': top_urls}, 
        index=MANAGEMENT_INDEX, doc_type=CONTENT_DOCUMENT_TYPE)
    matching_content = filter(lambda c: c['found'], content_res['docs'])

    # Also get a sample tweet related to each url
    related_tweet_ids = [url['tweet_ids']['buckets'][0]['key'] for url in res]
    related_tweet_res = es(universe).mget({'ids': related_tweet_ids},
        index=universe, doc_type=TWEET_DOCUMENT_TYPE)['docs']
    
    # Add some metadata, including the tweet
    top_content = []
    for index, item in enumerate(matching_content):
        source = item['_source']

        # Add the link's rank
        source['rank'] = index + 1

        # Add the first time the link was tweeted
        first_tweeted = first_tweeted_map[source['url']]
        source['first_tweeted'] = get_time_since_now(first_tweeted)

        try:
            # Add the sample related tweet we grabbed from the index
            tweet = filter(lambda t: t['_source']['content_url'] == source['url'], 
                related_tweet_res)[0]
        except IndexError:
            source['tweet'] = {}
        else:
            source['tweet'] = {
                'user_screen_name': tweet['_source']['user_screen_name'],
                'text': tweet['_source']['text'],
                'user_profile_image_url': tweet['_source']['user_profile_image_url']
            }
        top_content.append(source)
    return top_content


def get_top_providers(size=2000):
    """
    Get a list of all providers (i.e. domains) in order of popularity.
    Possible future use for autocomplete, to search across publications.
    """
    body = {
        'aggregations': {
            'providers': {
                'terms': {
                    'field': 'provider',
                    'size': size
                }
            }
        }
    }
    res = es_management().search(
        index=MANAGEMENT_INDEX, 
        doc_type=CONTENT_DOCUMENT_TYPE, 
        body=body, 
        size=0)
    return [i['key'] for i in res['aggregations']['providers']['buckets']]


def format_date(dt):
    """Convert a datetime to an elasticsearch-formatted datestring.
    Timezone-unaware, will search in UTC."""
    return dt.strftime('%a %b %d %H:%M:%S +0000 %Y')


def get_time_since_now(epoch):
    """
    Accepts a unix timestamp, and gets the number of 
    days/hours/minutes/seconds ago as a string.

    UTC only for now.
    """
    now = datetime.datetime.utcnow()
    then = datetime.datetime(*time.gmtime(epoch / 1000)[:7])
    diff = now - then
    time_map = (
        ('day', diff.days),
        ('hour', diff.seconds / 60 / 60),
        ('minute', diff.seconds / 60),
        ('second', diff.seconds)
    )
    # Loop through each amount, and if there are any, return its value
    for word, amt in time_map:
        if amt > 1:
            return "%d %ss" % (amt, word)
        elif amt == 1:
            return "%d %s" % (amt, word)
    # Since it goes down to seconds, you probably shouldn't get here
    return 'just now'
