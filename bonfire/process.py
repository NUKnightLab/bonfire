import time
from newspaper import Article
from .db import build_universe_mappings, build_url_cache_mappings, next_unprocessed_tweet, \
                save_tweet, save_url, get_cached_url, set_cached_url
from .url import start_session, resolve_url
from .content import extract

def process_universe_rawtweets(universe, build_mappings=True):
    """Takes all unprocessed tweets in given universe, extracts and processes its contents."""
    if build_mappings:
        build_universe_mappings()
        build_url_cache_mappings()
    while True:
        try:
            raw_tweet = next_unprocessed_tweet(universe)
        except:
            break
        process_rawtweet(universe, raw_tweet)

def process_rawtweet(universe, raw_tweet):
    """Saves a new tweet and extracts metadata from its URLs."""
    tweet = {
        'id': raw_tweet['_source']['id'],
        'id_str': raw_tweet['_source']['id_str'],
        'text': raw_tweet['_source']['text'],
        'created': raw_tweet['_source']['created_at'],
        'retweet_count': raw_tweet['_source']['retweet_count'],
        #'retweeted_status': raw_tweet['_source']['retweeted_status'],
        'user_id': raw_tweet['_source']['user']['id'],
        'user_name': raw_tweet['_source']['user']['name'],
        'user_screen_name': raw_tweet['_source']['user']['screen_name'],
        'user_profile_image_url': raw_tweet['_source']['user']['profile_image_url']
    }
    save_tweet(universe, tweet)

    urls = [u['expanded_url'] for u in raw_tweet['_source']['entities']['urls']]
    for url in filter(lambda u: get_cached_url(u) is None, urls):
        extracted_article = extract(url)
        set_cached_url(url, extracted_article['url'])
        extracted_article['tweet_id'] = tweet['id']
        save_url(universe, extracted_article)