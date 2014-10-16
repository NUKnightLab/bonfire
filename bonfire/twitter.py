import time
import logging
from elasticsearch.exceptions import ConnectionError, TransportError
from birdy.twitter import UserClient, StreamClient
from . import config
from .db import get_user_ids, enqueue_tweet


def logger():
    return logging.getLogger(__name__)


_clients = {}
def client(universe):
    """Return a Twitter client for the given universe."""
    global _clients
    if universe not in _clients:
        _clients[universe] = UserClient(*config.get_twitter_keys(universe))
    return _clients[universe]


_stream_clients = {}
def stream_client(universe):
    """Return a Twitter streaming client for the given universe."""
    global _stream_clients
    if universe not in _stream_clients:
        _stream_clients[universe] = StreamClient(
            *config.get_twitter_keys(universe))
    return _stream_clients[universe]


def tweet_link(universe, link):
    via = ' via @%s' % link['tweets'][0]['user_screen_name']
    text_limit = 140 - 23 - len(via)
    status = text[:text_limit] + ' ' + link['url'] + via
    client(universe).api.statuses.update.post(status=status)


def lookup_users(universe, usernames):
    """Lookup Twitter users by screen name. Limited to first 100 user
    names by API limitation."""
    if isinstance(usernames, basestring):
        usernames = [ usernames ]
    return client(universe).api.users.lookup.post(
        screen_name=','.join(usernames[:100])).data


def get_friends(universe, user_id):
    """Get Twitter IDs for friends of the given user_id."""
    return client(universe).api.friends.ids.get(
        user_id=user_id, stringify_ids=True).data.ids


def collect_seeded_universe_tweets(universe):
    """Connects to the streaming API and enqueues tweets from universe users.
    Limited to the top 5000 users by API limitation."""
    client = stream_client(universe)
    try:
        users = set(get_user_ids(universe, size=5000))
        logger().info('Connecting to universe %s with %d users' % (
            universe, len(users)))
        response = client.stream.statuses.filter.post(follow=','.join(users))
        for tweet in response.stream():
            if 'entities' in tweet \
                    and tweet['entities']['urls'] \
                    and tweet['user']['id_str'] in users:
                logger().debug('Enqueuing new tweet %s' % tweet['id_str'])
                enqueue_tweet(universe, tweet)
    except (ConnectionError, TransportError) as err:
        logger().warn(
            "Collector's connection to Elasticsearch failed: %s %s. Retrying." % 
            (type(err), err.message))
        time.sleep(5)
        return collect_universe_tweets(universe)


def collect_list_universe_tweets(universe):
    since_id = 0
    client_ = client(universe)
    while True:
        logger().debug('Checking for %s list update since ID: %d' % (
            universe, since_id))
        kw = config.get_list_config(universe)
        kw['count'] = 200   # Max allowable count is not documented. The
                            # same parameter for user status is documented as
                            # max value of 200, so we're going with that
        if since_id:
            kw['since_id'] = since_id
        response = client_.api.lists.statuses.get(**kw)
        for tweet in response.data:
            if 'entities' in tweet and tweet['entities']['urls']:
                logger().debug('Enqueuing new tweet %s' % tweet['id_str'])
                enqueue_tweet(universe, tweet)
                if tweet['id'] > since_id:
                    since_id = tweet['id']
        time.sleep(10)  # 10 seconds seems reasonable -- this should only use
                        # 1/2 of our rate limit (180 requests/15 minutes)
   

class UnsupportedUniverseType(Exception): pass


def collect_universe_tweets(universe): 
    type_ = config.get('universe:%s' % universe, 'type', default='seeded')
    if type_ == 'seeded':
        collect_seeded_universe_tweets(universe)
    elif type_ == 'list':
        collect_list_universe_tweets(universe)
    else:
        raise UnsupportedUniverseType(type_)
