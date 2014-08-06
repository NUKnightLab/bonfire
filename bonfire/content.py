import requests
from newspaper import Article
from newspaper.images import fetch_image_dimension
from urlparse import urlparse, urljoin

# These are url domains/excepts that newspaper's URL sanitizer handles poorly.
# Add to these flags if you want to keep request arguments, etc.
NEWSPAPER_FLAGS = set(('youtube.com'))

# Known url shortening domains.
# Newspaper sometimes assumes that shortened domains are canonical, so this
# list is here to catch any that shouldn't be included.
SHORT_URLS = set((
    '0rz.tw', '1link.in', '1url.com', '2.gp', '2big.at', '2tu.us', '3.ly',
    '307.to', '4ms.me', '4sq.com', '4url.cc', '6url.com', '7.ly', 'a.gg', 
    'a.nf', 'aa.cx', 'abcurl.net', 'ad.vu', 'adf.ly', 'adjix.com', 'afx.cc', 
    'all.fuseurl.com', 'alturl.com', 'amzn.to', 'ar.gy', 'arst.ch', 'atu.ca', 
    'azc.cc', 'b23.ru', 'b2l.me', 'bacn.me', 'bcool.bz', 'binged.it', 
    'bit.ly', 'bizj.us', 'bloat.me', 'bravo.ly', 'bsa.ly', 'budurl.com', 
    'canurl.com', 'chilp.it', 'chzb.gr', 'cl.lk', 'cl.ly', 'clck.ru', 
    'cli.gs', 'cliccami.info', 'clickthru.ca', 'clop.in', 'conta.cc', 
    'cort.as', 'cot.ag', 'crks.me', 'ctvr.us', 'cutt.us', 'dai.ly', 
    'decenturl.com', 'dfl8.me', 'digbig.com', 'digg.com', 'disq.us', 'dld.bz',
    'dlvr.it', 'do.my', 'doiop.com', 'dopen.us', 'easyuri.com', 'easyurl.net',
    'eepurl.com', 'eweri.com', 'fa.by', 'fav.me', 'fb.me', 'fbshare.me', 
    'ff.im', 'fff.to', 'fire.to', 'firsturl.de', 'firsturl.net', 'flic.kr', 
    'flq.us', 'fly2.ws', 'fon.gs', 'freak.to', 'fuseurl.com', 'fuzzy.to', 
    'fwd4.me', 'fwib.net', 'g.ro.lt', 'gizmo.do', 'gl.am', 'go.9nl.com', 
    'go.ign.com', 'go.usa.gov', 'goo.gl', 'goshrink.com', 'gurl.es', 'hex.io',
    'hiderefer.com', 'hmm.ph', 'href.in', 'hsblinks.com', 'htxt.it', 
    'huff.to', 'hulu.com', 'hurl.me', 'hurl.ws', 'icanhaz.com', 'idek.net', 
    'ilix.in', 'is.gd', 'its.my', 'ix.lt', 'j.mp', 'jijr.com', 'kl.am', 
    'klck.me', 'korta.nu', 'krunchd.com', 'l9k.net', 'lat.ms', 'liip.to', 
    'liltext.com', 'linkbee.com', 'linkbun.ch', 'liurl.cn', 
    'ln-s.net', 'ln-s.ru', 'lnk.gd', 'lnk.ms', 'lnkd.in', 'lnkurl.com', 
    'lru.jp', 'lt.tl', 'lurl.no', 'macte.ch', 'mash.to', 'merky.de', 
    'migre.me', 'miniurl.com', 'minurl.fr', 'mke.mmke.by.to', 'moourl.com', 
    'mrte.ch', 'myloc.mylocurl.in', 'n.pr', 'nbc.co', 'nblo.gs', 'nn.nf', 
    'not.my', 'notlong.com', 'nsfw.in', 'nutshellurl.com', 'nxy.in', 
    'nyti.ms', 'o-x.fr', 'oc1.us', 'om.ly', 'omf.gd', 'omoikane.net', 
    'on.cnn.com', 'on.mktw.net', 'onforb.es', 'orz.se', 'ow.ly', 'ping.fm', 
    'pli.gs', 'pnt.me', 'politi.co', 'post.ly', 'pp.gg', 'profile.to', 
    'ptiturl.com', 'pub.vitrue.com', 'qlnk.net', 'qte.me', 'qu.tc', 'qy.fi', 
    'r.im', 'rb6.me', 'read.bi', 'readthis.ca', 'reallytinyurl.com', 
    'redir.ec', 'redirects.ca', 'redirx.com', 'retwt.me', 'ri.ms', 
    'rickroll.it', 'riz.gd', 'rt.nu', 'ru.ly', 'rubyurl.com', 'rurl.org', 
    'rww.tw', 's4c.in', 's7y.us', 'safe.mn', 'sameurl.com', 'sdut.us', 
    'shar.es', 'shink.de', 'shorl.com', 'short.ie', 'short.to', 
    'shortlinks.co.uk', 'shorturl.com', 'shout.to', 'show.my', 
    'shrinkify.com', 'shrinkr.com', 'shrt.fr', 'shrt.st', 'shrten.com', 
    'shrunkin.com', 'simurl.com', 'slate.me', 'smallr.com', 'smsh.me', 
    'smurl.name', 'sn.im', 'snipr.sniprnipurl.com', 'snurl.com', 'sp2.ro', 
    'spedr.com', 'srnk.net', 'srs.li', 'starturl.com', 'su.pr', 'surl.co.uk', 
    'surl.hu', 't.t.t.t.t.t.lh.com', 'ta.gd', 'tbd.ly', 'tcrn.tcrn.tcme', 
    'tgr.ph', 'tighturl.com', 'tiniuri.com', 'tiny.cc', 'tiny.ly', 'tiny.pl', 
    'tinylink.in', 'tinyuri.ca', 'tinyurl.com', 'tk.', 'tl.gd', 'tmi.me', 
    'tnij.org', 'tnw.to', 'tny.com', 'to.ly', 'togoto.us', 'totc.us', 
    'toysr.us', 'tpm.ly', 'tr.im', 'tra.kz', 'trunc.it', 'twhub.com',
    'twirl.at', 'twitclicks.com', 'twitterurl.net', 'twitterurl.org', 
    'twiturl.de', 'twurl.cc', 'twurl.nl', 'u.mavrev.com', 'u.nu', 'u76.org', 
    'ub0.cc', 'ulu.lu', 'updating.me', 'ur1.ca', 'url.az', 'url.co.uk', 
    'url.ie', 'url360.me', 'url4.eu', 'urlborg.com', 'urlbrief.com', 
    'urlcover.com', 'urlcut.com', 'urlenco.de', 'urli.nl', 'urls.im', 
    'urlshorteningservicefortwitter.com', 'urlx.ie', 'urlzen.com', 'usat.ly', 
    'use.my', 'vb.ly', 'vgn.am', 'vl.am', 'vm.lc', 'w55.de', 'wapo.st', 
    'wapurl.co.uk', 'wipi.es', 'wp.me', 'x.vu', 'xr.com', 'xrl.in', 'xrl.us', 
    'xurl.es', 'xurl.jp', 'y.ahoo.it', 'yatuc.com', 'ye.pe', 'yep.it',
    'yfrog.com', 'yhoo.it', 'yiyd.com', 'youtu.be', 'yuarel.com', 'z0p.de', 
    'zi.ma', 'zi.mu', 'zipmyurl.com', 'zud.me', 'zurl.ws', 'zz.gd', 'zzang.kr'
    ))


def extract(url, html=None):
    """
    Extract metadata from a URL, and return a dict result.
    
    Uses newspaper `<https://github.com/codelucas/newspaper/>`_,
    but overrides some defaults in favor of opengraph and twitter elements.

    :arg html: if provided, skip downloading and go straight to parsing html.
    """
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

    image = f.get_image()
    result = {
        'url': f.get_canonical_url() or url.rstrip('/'),
        'provider': f.get_provider() or '',
        'title': f.get_title() or '',
        'description': f.get_description() or '',
        'text': article.text or '',
        #'published': f.get_published() or None,
        'authors': f.get_authors() or '',
        'img': image[0],
        'img_h': image[1],
        'img_w': image[2],
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
            self.resolved_url = requests.head(self.article.url, 
                timeout=7, allow_redirects=True).url
        return self.resolved_url

    def _add_domain(self, url):
        """Add the domain if the URL is relative."""
        if not url or url.startswith('http'):
            return url
        parsed_uri = urlparse(self.get_canonical_url())
        domain = "{uri.scheme}://{uri.netloc}".format(uri=parsed_uri)
        return urljoin(domain, url)

    def get_canonical_url(self):
        """
        Main function for determining the canonical url. Check as follows:
            - opengraph url (og:url)
            - twitter url (twitter:url)
            - newspaper's guess (usually from meta tags)

        If none of these work or newspaper guesses a short-url domain,
        it gives up and requests the url to get its final redirect.
        """
        canonical_url = self.article.meta_data.get('og', {}).get('url', '').strip() or\
                        self.article.meta_data.get('twitter', {}).get('url', '').strip() or\
                        self.article.canonical_link.strip()
        # Make sure it's not a short-url domain
        if not canonical_url or urlparse(canonical_url).netloc in SHORT_URLS:
            canonical_url = self._get_resolved_url()
        return canonical_url.rstrip('/')

    def get_provider(self):
        """Returns a prettified domain for the resource, stripping www."""
        return urlparse(self.get_canonical_url()).netloc.replace('www.', '')

    def get_title(self):
        """Retrieve title from opengraph, twitter, or meta tags."""
        return self.article.meta_data.get('og', {}).get('title', '').strip() or\
               self.article.meta_data.get('twitter', {}).get('title', '').strip() or\
               self.article.title.strip()

    def get_description(self):
        """Retrieve description from opengraph, twitter, or meta tags."""
        return self.article.meta_data.get('og', {}).get('description', '').strip() or\
               self.article.meta_data.get('twitter', {}).get('description', '').strip() or\
               self.article.summary.strip() or \
               self.article.meta_description.strip()

    def get_favicon(self):
        """Retrieve favicon url from article tags or from `<http://g.etfv.co>`_"""
        favicon_url = self.article.meta_favicon or \
                      'http://g.etfv.co/%s?defaulticon=none' % self.get_canonical_url()
        return self._add_domain(favicon_url)

    def get_twitter_player(self):
        """Retrieve default player for twitter cards."""
        player = self.article.meta_data.get('twitter', {}).get('player', '')
        if isinstance(player, dict):
            player = player.get('url', '') or player.get('src', '')
        return player

    def get_twitter_creator(self):
        """Retrieve twitter username of the creator."""
        creator = self.article.meta_data.get('twitter', {}).get('creator', '')
        if isinstance(creator, dict):
            creator = creator.get('url', '') or \
                      creator.get('src', '') or \
                      creator.get('id', '')
        return creator.lstrip('@')

    def get_twitter_image(self):
        """Retrieve twitter image for the resource."""
        img = self.article.meta_data.get('twitter', {}).get('image', '')
        height, width = 0, 0
        # Sometimes the image is at twitter:image:src rather than twitter:image
        if isinstance(img, dict):
            height = img.get('height', 0)
            width = img.get('width', 0)
            img = img.get('src', '') or \
                  img.get('url', '')
        return [img, height, width]

    def get_facebook_image(self):
        """Retrieve opengraph image for the resource."""
        img = self.article.meta_data.get('og', {}).get('image', '')
        height, width = 0, 0
        # Sometimes the image is at og:image:url rather than og:image
        if isinstance(img, dict):
            height = img.get('height', 0)
            width = img.get('width', 0)
            img = img.get('url', '') or \
                  img.get('src', '')
        return [img, height, width]

    def get_image_dimensions(self, img_url):
        return fetch_image_dimension(img_url, self.article.config.browser_user_agent)

    def get_image(self):
        """
        Retrieve a favorite image for the resource, checking in this order:
            - opengraph
            - twitter
            - newspaper's top image.
        """
        result = self.get_facebook_image() or \
                 self.get_twitter_image()
        if not result:
            result = [self.article.top_image, 0, 0]
        result[0] = self._add_domain(result[0])
        if not all(result[1:]):
            width, height = self.get_image_dimensions(result[0])
            result[1], result[2] = height, width
        return result

    def get_authors(self):
        """Retrieve an author or authors. This works very sporadically."""
        return ', '.join(self.article.authors) or \
               self.article.meta_data.get('og', {}).get('article', {}).get('author', '')

    def get_published(self):
        """Retrieve a published date. This almost never gets anything."""
        return self.article.published_date.strip() or \
               self.article.meta_data.get('og', {}).get('article', {}).get('published_time')

    def get_tags(self):
        """
        Retrive a comma-separated list of all keywords, categories, and tags, flattened:
            - opengraph tags + sections
            - keywords + meta_keywords
            - tags
        """
        og_results = self.article.meta_data.get('og', {}).get('tag', '').split(',') + \
                     [self.article.meta_data.get('og', {}).get('section', '')]
        all_candidates = list(set(self.article.keywords + \
            self.article.meta_keywords + list(self.article.tags) + og_results))
        return ', '.join(filter(lambda i: i, all_candidates))
