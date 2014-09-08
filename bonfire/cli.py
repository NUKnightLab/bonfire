import click
import logging.config
import os
import shutil
import sys
import ConfigParser
from pkg_resources import resource_string
from .config import (
    config_file_path,
    get_universes,
    logging_config,
    get_universes,
    BONFIRE_CONFIG_ENV_VAR)
from .db import (
    get_latest_tweet,
    get_latest_raw_tweet,
    delete_content_by_url,
    delete_tweets_by_url,
    build_universe_mappings )
from .universe import build_universe, cache_queries, cleanup_universe
from .twitter import collect_universe_tweets
from .process import process_universe_rawtweets


def yes_no(s):
    return s.lower().startswith('y')


def ensure_config():
    path = config_file_path()
    if not os.path.exists(path):
        inp = raw_input('\nInitial config file %s has not been created.' \
            '(Note: to change this path, set the %s environment variable)' \
            '\n\nCreate %s now? [Y/n] ' % (
            path, BONFIRE_CONFIG_ENV_VAR, path))
        if inp == '' or yes_no(inp):
            with open(path, 'w') as f:
                f.write(resource_string(__name__, 'bonfire.cfg'))
    if not os.path.exists(path):
        print('\nConfig file not found. Run `bonfire config` to create it.')
        sys.exit(0)
ensure_config()

logconf = logging_config()
UNIVERSES = get_universes()
if len(UNIVERSES) == 1:
    DEFAULT_UNIVERSE = UNIVERSES[0]
else:
    DEFAULT_UNIVERSE = None


if logconf.get('configfile'):
    configfile = logconf.pop('configfile')
    try:
        logging.config.fileConfig(configfile, defaults=logconf)
    except ConfigParser.NoSectionError, e:
        print('\nMissing or malformed logging configuration file: %s' %
            configfile)
        print(e)
        sys.exit(0)
else:
    logging.basicConfig(**logging_config())


def edit_file(filename):
    editor = os.getenv('EDITOR')
    if editor is None:
        click.echo('\nPlease set the EDITOR environment variable.\n\n')
        click.echo('e.g.:\n\n   >  export EDITOR=`which vi`')
        sys.exit(0)
    os.system('%s %s' % (editor, filename))


@click.group(context_settings={'help_option_names':['-h','--help']})
def cli():
    """Bonfire application management"""
    pass


@click.command()
def config():
    """Configure Bonfire."""
    edit_file(config_file_path())


@click.command()
def universes():
    """Display configured universes."""
    click.echo('\nUniverses defined in config file:')
    cf = config_file_path()
    click.echo(cf)
    click.echo('='*len(cf))
    for u in get_universes():
        click.echo(u)
    click.echo()


@click.command()
@click.argument('universe', default=DEFAULT_UNIVERSE,
    type=click.Choice(UNIVERSES))
def build(universe):
    """Build a universe from configured seed."""
    click.echo('Building universe: %s' % universe)
    build_universe(universe)


@click.command()
@click.argument('universe', default=DEFAULT_UNIVERSE,
    type=click.Choice(UNIVERSES))
def collect(universe):
    """Collect Tweets for a universe."""
    click.echo('Collecting universe: %s' % universe)
    collect_universe_tweets(universe)


@click.command()
@click.argument('universe', default=DEFAULT_UNIVERSE,
    type=click.Choice(UNIVERSES))
def process(universe):
    """Resolve, extract, and save tweets from a universe."""
    click.echo('Processing universe: %s' % universe)
    process_universe_rawtweets(universe)


@click.command()
@click.argument('universe', default=DEFAULT_UNIVERSE,
    type=click.Choice(UNIVERSES))
@click.option('--top_links', is_flag=True)
@click.option('--tweet', is_flag=True)
def cache(universe, top_links, tweet):
    """Cache common results from a universe."""
    click.echo('Caching universe: %s' % universe)
    cache_queries(universe, top_links=top_links, tweet=tweet)


@click.command()
@click.argument('universe', default=DEFAULT_UNIVERSE,
    type=click.Choice(UNIVERSES))
@click.option('--days', default=30,
    help='Number of days ago to consider something old.')
def cleanup(universe, days):
    """Delete old records from a universe index."""
    cleanup_universe(universe, days=days)


@click.command()
@click.argument('universe', default=DEFAULT_UNIVERSE)
def lasttweet(universe):
    """Show the latest processed tweet."""
    t = get_latest_tweet(universe)    
    if t is None:
        print '\nTweet Index Is Empty\n'
    else:
        print '\n@%s' % t.user_screen_name
        print t.text
        print t.created
        print ''


@click.command()
@click.argument('universe', default=DEFAULT_UNIVERSE)
def lastrawtweet(universe):
    """Show the latest unprocessed queued tweet."""
    t = get_latest_raw_tweet(universe)    
    if t is None:
        print '\nRaw Tweet Queue Is Empty\n'
    else:
        print '\n@%s' % t.user['screen_name']
        print t.text
        print t.created_at
        print ''

@click.command()
@click.argument('universe')
@click.argument('url')
def delete(universe, url):
    """Delete universe content and tweets specified by URL."""
    delete_content_by_url(universe, url)
    delete_tweets_by_url(universe, url)


@click.command()
@click.argument('universe', default=DEFAULT_UNIVERSE)
def remap(universe):
    """Delete universe data and rebuild mappings."""
    build_universe_mappings(universe, True)


@click.command()
@click.pass_context
def help(ctx):
    """Show help."""
    print(ctx.parent.get_help())



cli.add_command(config)
cli.add_command(universes)
cli.add_command(build)
cli.add_command(collect)
cli.add_command(process)
cli.add_command(cache)
cli.add_command(cleanup)
cli.add_command(lasttweet)
cli.add_command(lastrawtweet)
cli.add_command(delete)
cli.add_command(remap)
cli.add_command(help)
