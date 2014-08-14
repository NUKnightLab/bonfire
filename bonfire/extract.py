from __future__ import division
import urllib2
import re
import requests
from bs4 import BeautifulSoup
from delorean import parse as parse_date

ATTRIBUTION_REX = re.compile('^\s*[Bb][Yy]\s+(\w+\.? ?){1,4}\.?\s*$')
WORD = re.compile('\w+')
DEFAULT_CONTENT_NODE_TYPES = ['p']
HEADER_NODE_TYPES = ['h1', 'h2', 'h3']


def content_nodes(elem, node_types=None):
    if node_types is None:
        node_types = DEFAULT_CONTENT_NODE_TYPES
    return elem.find_all(node_types)


def word_count(text):
    return len(WORD.findall(text))


def link_density(obj):
    text = clean_whitespace(obj.get_text())
    text_word_count = word_count(text)
    links = obj.select('a')
    link_word_count = 0
    for l in links:
        linktext = clean_whitespace(l.get_text())
        link_word_count += word_count(linktext)
    return link_word_count / text_word_count


def find_pubdate(node):
    parent = node.parent
    return parent.find_all('time')[0].getText()


def is_attribution(string):
    if ATTRIBUTION_REX.match(string):
        return True
    return False


WHITESPACE = re.compile('\s+', re.M)
def clean_whitespace(string):
    return re.sub(WHITESPACE, ' ', string).strip()


def clean_attribution(string):
    string =  re.sub('\s+', ' ', string).strip()
    return re.sub('^[Bb][Yy] ', '', string)


def word_count(text):
    return len(text.split(' '))

UPDATED = re.compile('(?:last )?updated', re.I)
def as_date(node):
    text = clean_whitespace(node.get_text())
    text = re.sub(UPDATED, '', text)
    try:
        return parse_date(text)
    except ValueError:
        return None


class InstantiationError(Exception): pass


class ArticleExtractor(object):

    def __init__(self, url=None, html=None):
        if url is None and html is None:
            raise InstantiationError(
                'ArticleExtractor must be instantiated with '\
                'a URL or HTML content.')
        self._url = url
        self._html = html
        self._densities = {}
        self._article_node = None
        self._doc = None
        self._title = None
        self._author = None


    def fetch(self, url):
        return requests.get(url).text

    @property
    def url(self):
        return self._url
        
    @property
    def html(self):
        if self._html is None:
            self._html = self.fetch(self.url)
        return self._html

    @property
    def doc(self):
        if self._doc is None:
            self._doc = BeautifulSoup(self.html)
        return self._doc

    @property
    def article_node(self):
        if self._article_node is None:
            scores = {}
            nodes = None
            article = self.doc.select('article')
            if not article:
                article = self.doc.select('#article')
            if article:
                nodes = content_nodes(article[0])
            if not nodes:
                nodes = content_nodes(self.doc)
            for node in nodes:
                parent = node.parent
                if not parent in scores:
                    scores[parent] = 0.0
                density = link_density(node)
                wc = word_count(clean_whitespace(node.get_text()))
                scores[parent] += wc - wc * density
                self._densities[node] = density
            self._article_node = sorted(scores, key=scores.get, reverse=True)[0]
        return self._article_node

    def get_article_text(self):
        r = []
        for n in content_nodes(self.article_node):
            t = clean_whitespace(n.get_text())
            if all([
                    n in self._densities and self._densities[n] < .1,
                    word_count(t) > 3,
                    not is_attribution(t),
                    as_date(n) is None,
                    not '|' in t]):
                r.append(t)
        return r

    @property
    def title(self):
        if self._title is None:
            parent = self.article_node.parent
            for ht in HEADER_NODE_TYPES:
                headers = parent.find_all(ht)
                if headers:
                    self._title =  clean_whitespace(headers[0].get_text())
                    break
        if self._title is None:
            headers = self.doc.find_all(HEADER_NODE_TYPES)
            if headers:
                self._title = clean_whitespace(headers[0].get_text())
        return self._title


    def _author_helper(self, base_node):
        if self._author is None:
            parent = base_node
            for i, child in enumerate(parent.descendants):
                if hasattr(child, 'getText'):
                    if is_attribution(child.getText()):
                        self._author = clean_attribution(child.getText())
                        break
        if self._author is None:
            spans = parent.find_all(['span'], class_=re.compile('.*author.*'))
            if len(spans) > 0:
                self._author = clean_attribution(spans[0].get_text())
        if self._author is None:
            a = parent.find_all(['a'], rel=re.compile('.*author.*'))
            if len(a) > 0:
                self._author = clean_attribution(a[0].get_text())
        if self._author is None:
            ps = parent.find_all(['p'], class_=re.compile('.*author.*'))
            if len(ps) > 0:
                self._author = clean_attribution(ps[0].get_text())
        if self._author is None:
            divs = parent.find_all(['div'], class_=re.compile('.*author.*'))
            if len(divs) > 0:
                self._author = clean_attribution(divs[0].get_text())

    @property
    def author(self):
        if self._author is None:
            self._author_helper(self.article_node.parent)
        if self._author is None:
            self._author_helper(self.doc)
        return self._author


if __name__=='__main__':
    import sys
    url = sys.argv[1]
    extractor = ArticleExtractor(url=url)
    print 'TITLE:', extractor.title
    print 'AUTHOR:', extractor.author
    print 'TEXT'
    print '----'
    for t in extractor.get_article_text():
        print t
        print ''
