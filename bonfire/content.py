import requests
from newspaper import Article
from urlparse import urlparse, urljoin

# These are url domains/excepts that newspaper's URL sanitizer handles poorly.
# Add to these flags if you want to keep request arguments, etc.
NEWSPAPER_FLAGS = set(('youtube.com'))

def get_provider(url):
    return urlparse(url).netloc.replace('www.', '')

def extract(url, html=None):
    """Extracts metadata from a URL, and returns a dict result.
    Skips downloading step if html is provided."""

    article = Article(url)

    # Check for any flags that newspaper handles poorly.
    if html is None and any(item in url for item in NEWSPAPER_FLAGS):
        html = requests.get(url, timeout=7).text

    if html is None:
        article.download()
    else:
        article.set_html(html)
    article.parse()
    f = NewspaperFetcher(article)

    canonical_url = f.get_canonical_url() or url.rstrip('/')
    result = {
        'url': canonical_url,
        'provider': get_provider(canonical_url),
        'title': f.get_title() or '',
        'description': f.get_description() or '',
        'text': article.text or '',
        'published': f.get_published() or None,
        'authors': f.get_authors() or '',
        'img': f.get_image(),
        'player': f.get_twitter_player(),
        'favicon': f.get_favicon(),
        'tags': f.get_tags(),
        'opengraph_type': article.meta_data.get('og', {}).get('type', ''),
        'twitter_type': article.meta_data.get('twitter', {}).get('card', ''),
        'twitter_creator': f.get_twitter_creator()
    }
    return result

class NewspaperFetcher(object):
    """
    Smartly fetches metadata from a newspaper article, and cleans the results.
    """

    def __init__(self, newspaper_article):
        self.article = newspaper_article
        self.resolved_url = ''

    def _get_resolved_url(self):
        """Fallback in case newspaper can't find a good canonical url."""
        if not self.resolved_url:
            self.resolved_url = requests.head(self.article.url, timeout=7, allow_redirects=True).url
        return self.resolved_url

    def _add_domain(self, url):
        """Adds the domain if the URL is relative."""
        if url.startswith('http'):
            return url
        canonical_url = self.get_canonical_url()
        parsed_uri = urlparse(canonical_url)
        domain = "{uri.scheme}://{uri.netloc}".format(uri=parsed_uri)
        return urljoin(domain, url)

    def get_canonical_url(self):
        canonical_url = self.article.meta_data.get('og', {}).get('url', '').strip() or \
                        self.article.meta_data.get('twitter', {}).get('url', '').strip() or \
                        self.article.canonical_link.strip() or \
                        self._get_resolved_url()
        return canonical_url.rstrip('/')

    def get_title(self):
        return self.article.meta_data.get('og', {}).get('title', '').strip() or \
               self.article.meta_data.get('twitter', {}).get('title', '').strip() or \
               self.article.title.strip()

    def get_description(self):
        return self.article.meta_data.get('og', {}).get('description', '').strip() or \
               self.article.meta_data.get('twitter', {}).get('description', '').strip() or \
               self.article.summary.strip() or \
               self.article.meta_description.strip()

    def get_favicon(self):
        favicon_url = self.article.meta_favicon or \
                      'http://g.etfv.co/%s?defaulticon=none' % self.get_canonical_url()
        return self._add_domain(favicon_url)

    def get_twitter_player(self):
        player = self.article.meta_data.get('twitter', {}).get('player', '')
        if isinstance(player, dict):
            player = player.get('url', '') or player.get('src', '')
        return player

    def get_twitter_creator(self):
        creator = self.article.meta_data.get('twitter', {}).get('creator', '')
        if isinstance(creator, dict):
            creator = creator.get('url', '') or creator.get('src', '') or creator.get('id', '')
        return creator.lstrip('@')

    def get_twitter_image(self):
        img = self.article.meta_data.get('twitter', {}).get('image', '')
        # Sometimes the image is at "twitter:image:src" rather than "twitter:image"
        if isinstance(img, dict):
            img = img.get('src', '') or img.get('url', '')
        return img

    def get_facebook_image(self):
        img = self.article.meta_data.get('og', {}).get('image', '')
        if isinstance(img, dict):
            img = img.get('url', '') or img.get('src', '')
        return img

    def get_image(self):
        result = self.get_facebook_image() or \
                 self.get_twitter_image() or \
                 self.article.top_image
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
