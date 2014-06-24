from birdy.twitter import UserClient, StreamClient
from .config import get_twitter_keys
from .db import get_universe_users, enqueue_tweet


_clients = {}
def client(universe):
    """Return a Twitter client for the given universe."""
    global _clients
    if universe not in _clients:
        _clients[universe] = UserClient(*get_twitter_keys(universe))
    return _clients[universe]


_stream_clients = {}
def stream_client(universe):
    """Return a Twitter streaming client for the given universe."""
    global _stream_clients
    if universe not in _stream_clients:
        _stream_clients[universe] = StreamClient(*get_twitter_keys(universe))
    return _stream_clients[universe]


def lookup_users(universe, usernames):
    """Lookup Twitter users by screen name. Limited to first 100 user
    names by API limitation."""
    if isinstance(usernames, basestring):
        usernames == [ usernames ]
    return client(universe).api.users.lookup.post(
        screen_name=','.join(usernames)[:100]).data


def get_friends(universe, user_id):
    """Get Twitter IDs for friends of the given user_id."""
    return client(universe).api.friends.ids.get(user_id=user_id).data.ids


def collect_universe_tweets(universe):
    users = ','.join([str(u['_source']['id']) for u in
        get_universe_users(universe)])
    client = stream_client(universe)
    response = client.stream.statuses.filter.post(follow=users)
    for tweet in response.stream():
        if 'entities' in tweet and tweet['entities']['urls']:
            enqueue_tweet(universe, tweet)
