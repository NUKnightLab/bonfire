import requests
from newspaper import Article
from urlparse import urlparse, urljoin

# These are url domains/excepts that newspaper's URL sanitizer handles poorly.
# Add to these flags if you want to keep request arguments, etc.
NEWSPAPER_FLAGS = set(('youtube.com'))

def get_resolved_url(url, timeout=4):
    """Fallback in case newspaper can't find a canonical url."""
    return requests.head(url, timeout=timeout, allow_redirects=True).url

def get_provider(url):
    return urlparse(url).netloc.replace('www.', '')

def extract(url, html=None):
    """Extracts metadata from a URL, and returns a dict result.
    Skips downloading step if html is provided."""

    article = Article(url)

    # Check for any flags that newspaper handles poorly.
    if html is None and any(item in url for item in NEWSPAPER_FLAGS):
        html = requests.get(url, timeout=4).text

    if html is None:
        article.download()
    else:
        article.set_html(html)
    article.parse()
    f = NewspaperFetcher(article)

    canonical_url = f.get_canonical_url() or get_resolved_url(url) or url
    f.resolved_url = canonical_url
    result = {
        'url': canonical_url.rstrip('/'),
        'provider': get_provider(canonical_url),
        'title': f.get_title() or '',
        'description': f.get_description() or '',
        'text': article.text or '',
        'published': f.get_published() or None,
        'authors': f.get_authors() or '',
        'img': f.get_image(),
        'player': article.meta_data.get('twitter', {}).get('player', {}).get('url', ''),
        'favicon': f.get_favicon(),
        'tags': f.get_tags(),
        'opengraph_type': article.meta_data.get('og', {}).get('type', ''),
        'twitter_type': article.meta_data.get('twitter', {}).get('card', ''),
        'twitter_creator': article.meta_data.get('twitter', {}).get('creator', '').lstrip('@')
    }
    return result

class NewspaperFetcher(object):
    """
    Smartly fetches metadata from a newspaper article, and cleans the results.
    """

    def __init__(self, newspaper_article):
        self.article = newspaper_article
        self.resolved_url = ''

    def _add_domain(self, url):
        """Adds the domain if the URL is relative."""
        if url.startswith('http'):
            return url
        canonical_url = self.get_canonical_url()
        if not canonical_url:
            return canonical_url
        parsed_uri = urlparse(canonical_url)
        domain = "{uri.scheme}://{uri.netloc}".format(uri=parsed_uri)
        return urljoin(domain, url)

    def get_canonical_url(self):
        return self.article.canonical_link.strip() or \
               self.article.meta_data.get('og', {}).get('url', '').strip() or \
               self.article.meta_data.get('twitter', {}).get('url', '').strip() or \
               self.resolved_url

    def get_title(self):
        return self.article.title.strip() or \
               self.article.meta_data.get('og', {}).get('title', '').strip() or \
               self.article.meta_data.get('twitter', {}).get('title', '').strip()

    def get_description(self):
        return self.article.summary.strip() or \
               self.article.meta_description.strip() or \
               self.article.meta_data.get('og', {}).get('description', '') or \
               self.article.meta_data.get('twitter', {}).get('description', '')

    def get_favicon(self):
        favicon_url = self.article.meta_favicon or \
                      'http://g.etfv.co/%s?defaulticon=none' % self.get_canonical_url()
        return self._add_domain(favicon_url)

    def get_twitter_image(self):
        img = self.article.meta_data.get('twitter', {}).get('image', '')
        # Sometimes the image is at "twitter:image:src" rather than "twitter:image"
        if isinstance(img, dict):
            img = img['src']
        return img

    def get_image(self):
        result = self.article.top_image or \
                 self.article.meta_data.get('og', {}).get('image', '') or \
                 self.get_twitter_image()
        return self._add_domain(result)

    def get_published(self):
        return self.article.published_date.strip() or \
               self.article.meta_data.get('og', {}).get('article', {}).get('published_time')

    def get_authors(self):
        return ', '.join(self.article.authors) or \
               self.article.meta_data.get('og', {}).get('article', {}).get('author', '')

    def get_tags(self):
        """Retrives aggregate of all tags; opengraph tags/sections, keywords, meta_keywords, tags."""
        og_results = self.article.meta_data.get('og', {}).get('tag', '').split(',') + \
                     [self.article.meta_data.get('og', {}).get('section', '')]
        all_candidates = list(set(self.article.keywords + self.article.meta_keywords + list(self.article.tags) + og_results))
        return ', '.join(filter(lambda i: i, all_candidates))
