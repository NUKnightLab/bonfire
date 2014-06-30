from newspaper import Article
from .db import next_unprocessed_tweet, save_tweet, save_url, get_cached_url, set_cached_url
from .url import start_session, resolve_url
from .content import extract

def process_universe_rawtweets(universe, build_mappings=True):
    if build_mappings:
        build_url_cache_mappings()
    session = start_session()
    while True:
        try:
            raw_tweet = next_unprocessed_tweet(universe)
        except:
            break
        tweet = {
            'id': raw_tweet['_source']['id'],
            'text': raw_tweet['_source']['text'],
            'created': raw_tweet['_source']['created_at'],
            'user_id': raw_tweet['_source']['user']['id'],
            'user_name': raw_tweet['_source']['user']['name']
        }
        save_tweet(universe, tweet)

        urls = [u['expanded_url'] for u in raw_tweet['_source']['entities']['urls']]
        for url in filter(get_cached_url, urls):
            extracted_url = extract(url)
            set_cached_url(url, extracted_url['url'])
            extracted_url['tweet_id'] = tweet['id']
            save_url(universe, extracted_url)