from newspaper import Article
from .db import next_unprocessed_tweet, save_tweet
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
        unresolved_urls = [u['expanded_url'] for u in raw_tweet['_source']['entities']['urls']]
        resolved_urls = map(lambda url: resolve_url(url, session=session), unresolved_urls)
        extracted_content = map(extract, resolved_urls)
        # TODO: save in some format
        raw_tweet['content'] = extracted_content
        save_tweet()