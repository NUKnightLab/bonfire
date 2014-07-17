import time
from newspaper import Article
from .db import build_universe_mappings, build_management_mappings, next_unprocessed_tweet, \
                save_tweet, save_content, get_cached_url, set_cached_url
from .content import extract

def process_universe_rawtweets(universe, build_mappings=True):
    """Takes all unprocessed tweets in given universe, extracts and processes its contents."""
    if build_mappings:
        build_universe_mappings(universe)
        build_management_mappings()
    while True:
        raw_tweet = next_unprocessed_tweet(universe)
        if not raw_tweet:
            break
        process_rawtweet(universe, raw_tweet)

def process_rawtweet(universe, raw_tweet):
    """Saves a new tweet and extracts metadata from its URLs.
    Does not save if there are no URLs."""

    # First extract content
    urls = [u['expanded_url'] for u in raw_tweet['_source']['entities']['urls']]
    if not urls:
        return

    for url in urls:
        # Is ths url in our cache?
        resolved_url = get_cached_url(url)
        if resolved_url is None:
            # No-- go extract it
            try:
                article = extract(url)
            except Exception as e:
                print "%s %s" % (e, e.message)
                continue
            resolved_url = article['url']
            # Add it to the URL cache and save it
            set_cached_url(url, resolved_url)
            save_content(article)

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
    # Add the resolved URL from the extracted content. Only adds tweet's LAST URL.
    tweet['content_url'] = resolved_url
    save_tweet(universe, tweet)

