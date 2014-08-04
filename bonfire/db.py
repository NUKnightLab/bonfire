import math
import time
from elasticsearch import Elasticsearch
from elasticsearch.exceptions import NotFoundError, TransportError
from elasticsearch.helpers import bulk
from .config import get_elasticsearch_hosts
from .dates import ELASTICSEARCH_TIME_FORMAT, now, get_since_now, \
                   get_query_dates


RESULTS_CACHE_INDEX = 'bonfire_results_cache'
RESULTS_CACHE_DOCUMENT_TYPE = 'results'
RESULTS_CACHE_MAPPING = {
    'properties': {
        'cached_at': {
            'type': 'date',
            'format': ELASTICSEARCH_TIME_FORMAT
        },
        'hours_since': {
            'type': 'integer',
        },
        'results': {
            'properties': {
                '_default_': {
                    'type': 'string',
                    'index': 'no'
                },
                'score': {
                    'type': 'float',
                    'index': 'not_analyzed'
                }
            }
        }
    }
}

URL_CACHE_INDEX = 'bonfire_url_cache'
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

TOP_CONTENT_INDEX = 'bonfire_top_content'
TOP_CONTENT_DOCUMENT_TYPE = 'top_content'
TOP_CONTENT_MAPPING = {
    'properties': {
        '_default_': {
            'type': 'string',
            'index': 'no'
        },
        'tweet': {
            'properties': {
                'created': {
                    'type': 'date',
                    'format': ELASTICSEARCH_TIME_FORMAT
                }
            }
        }
    }
}

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

CONTENT_DOCUMENT_TYPE = 'content'
CONTENT_MAPPING = {
    'properties': {
        'url': {
            'type': 'string',
            'index': 'not_analyzed'
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
            'format': ELASTICSEARCH_TIME_FORMAT
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


def build_universe_mappings(universe):
    """Create and map the universe."""
    
    # Keys are the index names. 
    # Values are key/value pairs of the doc types and doc mappings.
    all_indices = {
        universe: {
            USER_DOCUMENT_TYPE: USER_MAPPING,
            CONTENT_DOCUMENT_TYPE: CONTENT_MAPPING,
            TWEET_DOCUMENT_TYPE: TWEET_MAPPING,
            UNPROCESSED_TWEET_DOCUMENT_TYPE: UNPROCESSED_TWEET_MAPPING
        },
        URL_CACHE_INDEX: {
            CACHED_URL_DOCUMENT_TYPE: CACHED_URL_MAPPING
        },
        RESULTS_CACHE_INDEX: {
            RESULTS_CACHE_DOCUMENT_TYPE: RESULTS_CACHE_MAPPING
        },
        TOP_CONTENT_INDEX: {
            TOP_CONTENT_DOCUMENT_TYPE: TOP_CONTENT_MAPPING
        }
    }

    for index_name, index_mapping in all_indices.items():
        if not es(universe).indices.exists(index_name):
            es(universe).indices.create(index=index_name)
        for doc_type, doc_mapping in index_mapping.items():
            es(universe).indices.put_mapping(
                doc_type, doc_mapping, index=index_name)


def get_all_docs(universe, index, doc_type, body={}, size=None, field='_id'):
    """
    Helper function to return all values in a certain field.
    Defaults to retrieving all ids from a given index and doc type.

    :arg universe: current universe.
    :arg index: current index.
    :arg doc_type: the type of doc to return all values for.
    :arg body: add custom body, or leave blank to retrieve everything.
    :arg size: limit by size, or leave as None to retrieve all.
    :arg field: retrieve all of a specific field. Defaults to id.
    """
    chunk_size, start = 5000, 0
    all_results = []
    while True:
        if field == '_id':
            res = es(universe).search(index=universe, doc_type=doc_type,
                body=body, size=chunk_size, from_=start,
                _source=False)
            all_results.extend(
                [u['_id'] for u in res['hits']['hits']])
        else:
            res = es(universe).search(index=universe, doc_type=doc_type,
                body=body, size=chunk_size, from_=start,
                _source_include=[field])
            all_results.extend(
                [u['_source'][field] for u in res['hits']['hits']])
        if size is None:
            size = res['hits']['total']
        start += chunk_size
        if start >= size:
            break
    return all_results


def cleanup(universe, days=30):
    """Delete everything in the universe that is more than days old.
    Does not apply to top content."""
    client = es(universe)
    actions = []

    body = {
        'filter': {
            'range': {
                'created': {
                    'lt': 'now-%dd' % days
                }
            }
        }
    }

    # Delete all tweets that are over days old
    old_tweet_ids = get_all_docs(universe,
        index=universe,
        doc_type=TWEET_DOCUMENT_TYPE,
        body=body)
    for tweet_id in old_tweet_ids:
        actions.append({
            '_op_type': 'delete',
            '_index': universe,
            '_type': TWEET_DOCUMENT_TYPE,
            '_id': tweet_id,
        })

    # Delete old cached results and urls
    body['filter']['range']['cached_at'] = body['filter']['range'].pop('created')
    old_results_ids = get_all_docs(universe,
        index=RESULTS_CACHE_INDEX,
        doc_type=RESULTS_CACHE_DOCUMENT_TYPE,
        body=body)
    for result_id in old_results_ids:
        actions.append({
            '_op_type': 'delete',
            '_index': RESULTS_CACHE_INDEX,
            '_type': RESULTS_CACHE_DOCUMENT_TYPE,
            '_id': result_id
        })
    old_urls_ids = get_all_docs(universe,
        index=URL_CACHE_INDEX,
        doc_type=URL_CACHE_DOCUMENT_TYPE,
        body=body)
    for url in old_urls_ids:
        actions.append({
            '_op_type': 'delete',
            '_index': URL_CACHE_INDEX,
            '_type': URL_CACHE_DOCUMENT_TYPE,
            '_id': url
        })

    # This actually deletes everything
    bulk(client, actions)

    # Now we can quickly get all content that doesn't have a tweet
    all_urls = set(get_all_docs(universe, 
        index=universe, 
        doc_type=CONTENT_DOCUMENT_TYPE))
    tweeted_urls = set(get_all_docs(universe,
        index=universe,
        doc_type=TWEET_DOCUMENT_TYPE,
        field='content_url'))
    obsolete_urls = all_urls - tweeted_urls

    # Delete those too
    actions = []
    for url in obsolete_urls:
        actions.append({
            '_op_type': 'delete',
            '_index': universe,
            '_type': CONTENT_DOCUMENT_TYPE,
            '_id': url
            })
    bulk(client, actions)
    

def get_cached_url(universe, url):
    """Get a resolved URL from the index.
    Returns None if URL doesn't exist."""
    try:
        return es(universe).get_source(index=URL_CACHE_INDEX, 
            id=url.rstrip('/'), doc_type=CACHED_URL_DOCUMENT_TYPE)['resolved']
    except NotFoundError:
        return None


def set_cached_url(universe, url, resolved_url):
    """Index a URL and its resolution in Elasticsearch"""
    body = {
        'url': url.rstrip('/'),
        'resolved': resolved_url.rstrip('/'),
        'cached_at': now(stringify=True)
    }
    es(universe).index(index=URL_CACHE_INDEX,
        doc_type=CACHED_URL_DOCUMENT_TYPE, body=body, id=url)



def add_to_results_cache(universe, hours, results):
    """Cache a set of results under certain number of hours."""
    body = {
        'cached_at': now(stringify=True),
        'hours_since': hours,
        'results': results
    }
    es(universe).index(
        index=RESULTS_CACHE_INDEX,
        doc_type=RESULTS_CACHE_DOCUMENT_TYPE,
        body=body)


def get_score_stats(universe, hours=4):
    """Get extended stats on the scores returned from the results cache.
    :arg hours: type of query to search for."""
    body = {
        'aggregations': {
            'fresh_queries': {
                'filter': {
                    'term': {
                        'hours_since': hours
                    }
                },
                'aggregations': {
                    'scores': {
                        'extended_stats': {
                            'field': 'score'
                        }
                    }
                }
            }
        }
    }
    res = es(universe).search(
        index=RESULTS_CACHE_INDEX, 
        doc_type=RESULTS_CACHE_DOCUMENT_TYPE, 
        body=body)
    return res['aggregations']['fresh_queries']['scores']


def get_top_link(universe, hours=4, quantity=5):
    """Search for any links in the current set that are a high enough score
    to get into top links. Return one (and only one) if so."""
    try:
        top_links = get_items(universe, hours=hours, quantity=quantity)
    except IndexError:
        return None
    score_stats = get_score_stats(universe, hours=hours)
    # Treat a link as a top link if it's > 2 standard devs above the average
    cutoff = score_stats['avg'] + (2 * score_stats['std_deviation'])
    link_is_already_top = lambda link: es(universe).exists(
        index=TOP_CONTENT_INDEX, 
        doc_type=TOP_CONTENT_DOCUMENT_TYPE, 
        id=link['url'])
    for link in top_links:
        if link['score'] >= cutoff and not link_is_already_top(link):
            # We only want one at a time even if more than 1 are in the results
            return link
    return None


def add_to_top_links(universe, link):
    """Index a new top link to the given universe."""
    es(universe).index(
        index=TOP_CONTENT_INDEX, 
        doc_type=TOP_CONTENT_DOCUMENT_TYPE,
        id=link['url'],
        body=link)


def get_recent_top_links(universe, quantity=20):
    """Get the most recently added top links in the given universe."""
    body = {
        'sort': [{
            'tweet.created': {
                'order': 'desc'
            }
        }]
    }
    res = es(universe).search(index=TOP_CONTENT_INDEX, 
        doc_type=TOP_CONTENT_DOCUMENT_TYPE, body=body, size=quantity)
    return [r['_source'] for r in res['hits']['hits']]


def save_content(universe, content):
    """Save the content of a URL to the index."""
    es(universe).index(index=universe,
        doc_type=CONTENT_DOCUMENT_TYPE,
        id=content['url'],
        body=content)


def delete_user(universe, user_id):
    """Delete a user from the universe index by their id."""
    es(universe).delete(index=universe, 
        doc_type=USER_DOCUMENT_TYPE, id=user_id)


def save_user(universe, user):
    """Check if a user exists in the database. If not, create it.
    If so, update it."""
    kwargs = {
        'index': universe,
        'doc_type': USER_DOCUMENT_TYPE,
        'id': user.get('id_str', user.get('id')),
    }
    if es(universe).exists(**kwargs):
        kwargs['body'] = {'doc': user}
        es(universe).update(**kwargs)
    else:
        kwargs['body'] = user
        es(universe).index(**kwargs)


def get_user_ids(universe, size=None):
    """Get top users for the universe by weight.
    :arg size: number of users to get. Defaults to all users."""
    body = {
        'sort': [{
            'weight': {
                'order': 'desc'
            }
        }]
    }
    user_ids = get_all_docs(universe, 
        index=universe, 
        doc_type=USER_DOCUMENT_TYPE,
        body=body,
        size=size)
    return user_ids


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


def get_universe_tweets(universe, query=None, quantity=20, 
                        hours=24, start=None, end=None):
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

    start, end = get_query_dates(start, end, hours)

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
                'gte': start,
                'lte': end
            }
        }
    }
    res = es(universe).search(index=universe, doc_type=TWEET_DOCUMENT_TYPE,
        body=body, size=quantity)
    return [tweet['_source'] for tweet in res['hits']['hits']]


def search_content(universe, query, size=100):
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
    res = es(universe).search(index=universe, doc_type=CONTENT_DOCUMENT_TYPE,
        body=body, size=size)
    return [content['_source'] for content in res['hits']['hits']]


def search_items(universe, term, quantity=100):
    """
    Search the text of both tweets and content for a given term and universe,
    and return some items matching one or the other.

    :arg term: search term to use for querying both tweets and content
    :arg quantity: number of items to return
    """

    # Search tweets and content for the given term
    body = {
        'query': {
            'multi_match': {
                'query': term,
                'fields': ['title', 'description', 'text']
            }
        }
    }
    res = es(universe).search(
        index=universe, 
        doc_type=','.join((CONTENT_DOCUMENT_TYPE, TWEET_DOCUMENT_TYPE)), 
        body=body, 
        size=quantity)['hits']['hits']

    formatted_results = []
    for index, hit in enumerate(res):
        result = hit['_source']
        if hit['_type'] == CONTENT_DOCUMENT_TYPE:
            matching_tweets = filter(
                lambda r: 'content_url' in r['_source'] and \
                          r['_source']['content_url'] == result['url'],
                res[index+1:])
            if matching_tweets:
                for tweet in matching_tweets:
                    popped_tweet = res.pop(res.index(tweet))
                    if not result.get('tweet'):
                        result['tweet'] = popped_tweet['_source']
        else:
            try:
                matching_content = filter(
                    lambda r: 'url' in r['_source'] and 
                              r['_source']['url'] == result['content_url'],
                    res[index+1:])[0]
            except IndexError:
                result = {
                    'type': 'tweet',
                    'url': result['content_url'],
                    'tweet': result
                    }
            else:
                tweet = result
                result = res.pop(res.index(matching_content))['_source']
                result['type'] = 'content'
                result['tweet'] = tweet
        result['rank'] = index + 1
        formatted_results.append(result)

    return formatted_results


def get_user_weights(universe, user_ids):
    """Takes a list of user ids and returns a dict 
    with their weighted influence."""
    res = es(universe).mget({'ids': list(set(user_ids))}, 
        index=universe, doc_type=USER_DOCUMENT_TYPE)['docs']
    users = filter(lambda u: u['found'], res)

    normalize_weight = lambda weight: math.log(weight*10) + 1
    user_weights = dict([
        (user['_source']['id'], normalize_weight(user['_source']['weight']))
        for user in users])
    return user_weights


def score_link(link, user_weights, time_decay=True, hours=24):
    """Scores a given link returned from elasticsearch.

    :arg link: full elasticsearch result for the link
    :arg user_weights: a dict with key,value pairs
        key is the user's id, value is the user's weighted twitter influence
    :arg time_decay: whether or not to decay the link's score based on time
    :arg hours: used for determining the decay factor if decay is enabled
    """
    score = 0.0
    score_explanation = []
    for tweeter in link['tweeters']['buckets']:
        # if they aren't in user_weights, they're no longer in the universe
        tweeter_influence = user_weights.get(tweeter['key'], 0.0)
        score += tweeter_influence
        score_explanation.append(
            'citizen %s with influence %.3f raises score to %.3f' % \
            (tweeter['key'], tweeter_influence, score))
    if time_decay:
        score_factor = lambda hrs_since: 1 - math.log(hrs_since + 1) / hours

        first_tweeted = link['first_tweet']['hits']['hits'][0]['sort'][0]
        hours_since = get_since_now(first_tweeted, 
            time_type='hour', stringify=False)[0]
        orig_score = score
        score *= score_factor(hours_since)
        score_explanation.append(
            'decay for %d hours drops score to %.3f (%.3f of original)' %\
            (hours_since, score, score/orig_score))
    return score, score_explanation


def get_items(universe, quantity=20, hours=24, 
              start=None, end=None, time_decay=True):
    """
    The default function: gets the most popular links shared 
    from a given universe and time frame.

    :arg quantity: number of links to return
    :arg hours: hours since end to search through.
    :arg start: start datetime in UTC. Defaults to hours.
    :arg end: end datetime in UTC. Defaults to now.
    :arg time_decay: whether or not to decay the score based on the time
        of its first tweet.
    """

    start, end = get_query_dates(start, end, hours)
    search_limit = quantity * 5 if time_decay else quantity * 2

    # Get the top links in the given time frame, and some extra agg metadata
    body = {
        'aggregations': {
            'recent_tweets': {
                'filter': {
                    'range': {
                        'created': {
                            'gte': start,
                            'lte': end
                        }
                    }
                },
                'aggregations': {
                    CONTENT_DOCUMENT_TYPE: {
                        'terms': {
                            'field': 'content_url',
                            # This orders by doc count, but we want the
                            # number of (unique) users tweeting it, weighted
                            # by influence. Is there any way to sub-aggregate
                            # that data and order it here?
                            'order': {
                                '_count': 'desc'
                            },
                            # Get extra docs because we need to reorder them
                            'size': search_limit,
                            'min_doc_count': 2,
                        },
                        'aggregations': {
                            'tweeters': {
                                'terms': {
                                    'field': 'user_id',
                                    'size': 1000
                                }
                            },
                            'first_tweet': {
                                'top_hits': {
                                    'size': 1,
                                    'sort': [{
                                        'created': {
                                            'order': 'asc'
                                        }
                                    }]
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
    links = res['aggregations']['recent_tweets'][CONTENT_DOCUMENT_TYPE]['buckets']
    if not links:
        # There's no content in the given time frame
        return []

    # Score each link based on its tweeters' relative influences, and time since
    tweeter_ids = [item for sublist in 
        [[i['key'] for i in link['tweeters']['buckets']] for link in links] 
        for item in sublist]
    user_weights = get_user_weights(universe, tweeter_ids)
    for link in links:
        link['score'], link['score_explanation'] = score_link(
                link, user_weights, time_decay=time_decay, hours=hours)
    sorted_links = sorted(links, 
        key=lambda link: link['score'], reverse=True)[:quantity]

    # Get the full metadata for these urls.
    top_urls = [url['key'] for url in sorted_links]
    link_res = es(universe).mget({'ids': top_urls}, 
        index=universe, doc_type=CONTENT_DOCUMENT_TYPE)
    matching_links = filter(lambda c: c['found'], link_res['docs'])

    # Add some metadata, including the tweet
    top_links = []
    for index, item in enumerate(matching_links):
        link = item['_source']
        # Add the link's rank
        link['rank'] = index + 1

        # Add the first time the link was tweeted, and the score
        link_match = filter(lambda l: l['key'] == link['url'], links)[0]
        link['score'] = link_match['score']
        link['score_explanation'] = link_match['score_explanation']
        
        tweet = link_match['first_tweet']['hits']['hits'][0]
        link['first_tweeted'] = get_since_now(tweet['sort'][0])
        link['tweet'] = tweet['_source']
        top_links.append(link)
    return top_links


def get_top_providers(universe, size=2000):
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
    res = es(universe).search(
        index=universe, 
        doc_type=CONTENT_DOCUMENT_TYPE, 
        body=body, 
        size=0)
    return [i['key'] for i in res['aggregations']['providers']['buckets']]

