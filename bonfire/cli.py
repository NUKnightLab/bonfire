import click
import logging.config
import os
import shutil
import sys
import ConfigParser
from .config import config_file_path, get_universes, logging_config
from .universe import build_universe
from .twitter import collect_universe_tweets
from .process import process_universe_rawtweets

logconf = logging_config()

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
@click.argument('universe')
def build(universe):
    """Build a universe from configured seed."""
    build_universe(universe)


@click.command()
@click.argument('universe')
def collect(universe):
    """Collect Tweets for a universe."""
    collect_universe_tweets(universe)


@click.command()
@click.argument('universe')
def process(universe):
    """Resolve, extract, and save tweets from a universe."""
    process_universe_rawtweets(universe)


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
cli.add_command(help)
