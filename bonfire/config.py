import collections
import ConfigParser
import os
import re
import sys

BONFIRE_CONFIG_ENV_VAR = 'BONFIRE_CONFIG'
INTERNAL_CONFIG_DIR = 'config'
INTERNAL_CONFIG_FILE = 'bonfire.cfg'
CONFIG_LIST_REGEX = re.compile(r'[, \s]+')


_config = None
def configuration():
    global _config
    if _config is None:
        _config = ConfigParser.ConfigParser()
        with open(config_file_path()) as f:
            _config.readfp(f)
    return _config


def config_file_path():
    return os.getenv(BONFIRE_CONFIG_ENV_VAR,
        os.path.join(sys.prefix, INTERNAL_CONFIG_DIR, INTERNAL_CONFIG_FILE))
    

def get_universe_seed(universe):
    config = configuration()
    seed = config.get('universe:%s' % universe, 'seed')
    return [s.strip() for s in CONFIG_LIST_REGEX.split(seed) if s.strip()]


def get_universes():
    config = configuration()
    return [section.split(':')[-1] for section in configuration().sections() if
        section.startswith('universe:')]


def get_twitter_keys(universe):
    config = configuration()
    TwitterKeys = collections.namedtuple('TwitterKeys', [
        'consumer_key',
        'consumer_secret',
        'access_token',
        'access_token_secret'])
    section = 'universe:%s' % universe
    k = TwitterKeys(
        config.get(section, 'twitter_consumer_key'),
        config.get(section, 'twitter_consumer_secret'),
        config.get(section, 'twitter_access_token'),
        config.get(section, 'twitter_access_token_secret'))
    return k


def get_elasticsearch_hosts(universe=None):
    config = configuration()
    if universe is None:
        hosts = config.get('bonfire', 'elasticsearch_hosts')
    else:
        hosts = config.get('universe:%s' % universe, 'elasticsearch_hosts')
    return [s.strip() for s in CONFIG_LIST_REGEX.split(hosts) if s.strip()]

