import logging
import time
from collections import deque
import requests
from elasticsearch.exceptions import ConnectionError, TransportError
from .db import build_universe_mappings, next_unprocessed_tweet, \
                save_tweet, save_content, get_cached_url, set_cached_url
from .content import extract
from .dates import get_since_now

USER_AGENT = 'Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)'

def logger():
    return logging.getLogger(__name__)


def create_session():
    """Create a requests session optimized for many connections."""
    session = requests.Session()
    session.headers['User-Agent'] = USER_AGENT
    session.max_redirects = 5
    http_adapter = requests.adapters.HTTPAdapter()
    https_adapter = requests.adapters.HTTPAdapter()
    http_adapter.pool_connections = 20
    http_adapter.pool_maxsize = 20
    http_adapter.max_retries = 1
    https_adapter.pool_connections = 20
    https_adapter.pool_maxsize = 20
    https_adapter.max_retries = 1
    session.mount('http://', http_adapter)
    session.mount('https://', https_adapter)
    return session


def process_universe_rawtweets(universe, build_mappings=True):
    """
    Take all unprocessed tweets in given universe, extract and process their
    contents.  When there are no tweets, sleep until it sees a new one.
    """
    logger().info('Processing universe %s' % universe)
    if build_mappings:
        logger().info('Building the universe.')
        build_universe_mappings(universe)
    recent_tweets = deque([], 5)
    session = create_session()
    while True:
        try:
            logger().debug('Looking for new tweet.')
            raw_tweet = next_unprocessed_tweet(universe, not_ids=list(recent_tweets))
            if raw_tweet:
                recent_tweets.append(raw_tweet._id)
                seconds_ago = get_since_now(
                    raw_tweet.created_at, 'second', stringify=False)[0]
                logger().debug(
                    'New tweet %d seconds ago. Processing.' % seconds_ago)
                if seconds_ago > 300:
                    logger().warn(
                        'Processor is %d seconds behind collector.' % \
                        seconds_ago)
                process_rawtweet(universe, raw_tweet, session=session)
            else:
                session.close()
                logger().debug('No new tweet. Waiting.')
                # Wait for a new tweet
                time.sleep(5)
        except (ConnectionError, TransportError) as err:
            logger().warn(
                "Processor's connection to Elasticsearch failed: %s %s. Retrying." % 
                (type(err), err.message))
            time.sleep(5)
            break
    session.close()
    logger().info('Retrying.')
    return process_universe_rawtweets(universe, build_mappings=False)


def process_rawtweet(universe, raw_tweet, session=None):
    """
    Take a raw tweet from the queue, extract and save metadata from its content,
    then save as a processed tweet.
    """
    if session is None:
        session = create_session()
    # First extract content
    urls = [u['expanded_url'] for u in raw_tweet.entities['urls']]
    for url in urls:
        # Is ths url in our cache?
        resolved_url = get_cached_url(universe, url)
        if resolved_url is None:
            # No-- go extract it
            try:
                response = session.get(url, timeout=7)
            except Exception as e:
                logger().info("Failed to access url %s due to %s, message %s" % (
                    url, e, e.message))
                continue
            try:
                article = extract(response.url, html=response.text)
            except requests.exceptions.Timeout:
                continue
            except requests.exceptions.TooManyRedirects:
                continue
            except requests.exceptions.ConnectionError:
                continue
            except requests.exceptions.HTTPError:
                continue
            except RuntimeError as e:
                # Not sure why this recursion error is happening
                if e.message == 'maximum recursion depth exceeded':
                    response.connection.close()
                    continue
                else:
                    logger().info("Failed to process url %s due to %s, message %s" % (
                        url, e, e.message))
                    continue
            except Exception as e:
                logger().info("Failed to process url %s due to %s, message %s" % (
                    url, e, e.message))
                response.connection.close()
                continue
            resolved_url = article['url']
            # Add it to the URL cache and save it
            set_cached_url(universe, url, resolved_url)
            save_content(universe, article)

    tweet = {
        'id': raw_tweet.id_str,
        'text': raw_tweet.text,
        'created': raw_tweet.created_at,
        'retweet_count': raw_tweet.retweet_count,
        #'retweeted_status': raw_tweet.retweeted_status,
        'user_id': raw_tweet.user['id_str'],
        'user_name': raw_tweet.user['name'],
        'user_screen_name': raw_tweet.user['screen_name'],
        'user_profile_image_url': raw_tweet.user['profile_image_url']
    }
    # Add the resolved URL from the extracted content. Only adds tweet's LAST URL.
    tweet['content_url'] = resolved_url
    save_tweet(universe, tweet)
