from newspaper import Article
from urlparse import urlparse, urljoin


def extract(url):
    article = Article(url)
    article.download()
    article.parse()
    f = NewspaperFetcher(article)

    result = {
        'orig_url': url,
        'url': f.get_canonical() or '',
        'title': f.get_title() or '',
        'description': f.get_description() or '',
        'published': f.get_published() or '',
        'authors': f.get_authors() or '',
        'img': f.get_image(),
        'player': article.meta_data['twitter'].get('player', ''),
        'favicon': f.get_favicon(),
        'raw_html': article.html,
        'tags': f.get_tags(),
        'og_type': article.meta_data['og'].get('type'),
        'twitter_type': article.meta_data['twitter'].get('card'),
        'twitter_creator': article.meta_data['twitter'].get('creator', '').lstrip('@')
    }
    return result

class NewspaperFetcher(object):

    def __init__(self, newspaper_article):
        self.article = newspaper_article

    def add_domain(self, url):
        if url.startswith('http'):
            return url
        parsed_uri = urlparse(self.get_canonical())
        domain = "{uri.scheme}://{uri.netloc}".format(uri=parsed_uri)
        return urljoin(domain, url)

    def get_canonical(self):
        return self.article.canonical_link.strip() or \
               self.article.meta_data['og'].get('url').strip() or \
               self.article.meta_data['twitter'].get('url').strip()

    def get_title(self):
        return self.article.title.strip() or \
               self.article.meta_data['og'].get('title').strip() or \
               self.article.meta_data['twitter'].get('title').strip()

    def get_description(self):
        return self.article.summary.strip() or \
               self.article.meta_description.strip() or \
               self.article.meta_data['og'].get('description') or \
               self.article.meta_data['twitter'].get('description')
    
    def get_twitter_image(self):
        img = self.article.meta_data['twitter'].get('image')
        if isinstance(img, dict):
            img = img['src']
        return img

    def get_favicon(self):
        return self.add_domain(self.article.meta_favicon)

    def get_image(self):
        result = self.article.top_image or \
                 self.article.meta_data['og'].get('image') or \
                 self.get_twitter_image()
        return self.add_domain(result)

    def get_published(self):
        return self.article.published_date.strip() or \
               self.article.meta_data['og'].get('article', {}).get('published_time')

    def get_authors(self):
        return ', '.join(self.article.authors) or \
               self.article.meta_data['og'].get('article', {}).get('author')

    def get_tags(self):
        og_results = self.article.meta_data['og'].get('tag', '').split(',') + \
                     [self.article.meta_data['og'].get('section', '')]
        all_candidates = list(set(self.article.keywords + self.article.meta_keywords + list(self.article.tags) + og_results))
        return ', '.join(filter(lambda i: i, all_candidates))

