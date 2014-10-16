import collections
import ConfigParser
import logging
import os
import re
import sys
from os.path import expanduser

BONFIRE_CONFIG_ENV_VAR = 'BONFIRE_CONFIG'
DEFAULT_CONFIG_DIR = expanduser('~')
DEFAULT_CONFIG_FILE = 'bonfire.cfg'
CONFIG_LIST_REGEX = re.compile(r'[, \s]+')


_config = None
def configuration():
    global _config
    if _config is None:
        _config = ConfigParser.SafeConfigParser()
        path = config_file_path()
        with open(path) as f:
            _config.readfp(f)
    return _config


def get(section, option, default=None):
    try:
        return configuration().get(section, option)
    except ConfigParser.NoOptionError:
        return default


def config_file_path():
    return os.getenv(BONFIRE_CONFIG_ENV_VAR,
        os.path.join(DEFAULT_CONFIG_DIR, DEFAULT_CONFIG_FILE))


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
    if not config.has_section(section):
        section = 'list:%s' % universe
    k = TwitterKeys(
        config.get(section, 'twitter_consumer_key'),
        config.get(section, 'twitter_consumer_secret'),
        config.get(section, 'twitter_access_token'),
        config.get(section, 'twitter_access_token_secret'))
    return k


def get_elasticsearch_hosts(universe):
    config = configuration()
    universe = 'universe:%s' % universe
    hosts = config.get(universe, 'elasticsearch_hosts')
    return [s.strip() for s in CONFIG_LIST_REGEX.split(hosts) if s.strip()]


def logging_config():
    config = configuration()
    try:
        return {
            'configfile': get('logging', 'configfile'),
            'filename': get('logging', 'filename'),
            'level': get('logging', 'level', 'INFO'),
            'filemode': get('logging', 'filemode', 'a'),
            'format': get('logging', 'format',
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'),
            'datefmt': get('logging', 'datefmt'),
        }
    except ConfigParser.NoSectionError:
        return {}


def get_list_config(universe):
    config = configuration()
    section = 'universe:%s' % universe
    return {
        'list_id': get(section, 'list_id'),
        'slug': get(section, 'slug'),
        'owner_screen_name': get(section, 'owner_screen_name'),
        'owner_id': get(section, 'owner_id')
    }
