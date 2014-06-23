import click
import os
import shutil
import sys
from .config import config_file_path, get_universes
from .universe import build_universe


def edit_file(filename):
    editor = os.getenv('EDITOR')
    if editor is None:
        click.echo('\nPlease set the EDITOR environment variable.\n\n')
        click.echo('e.g.:\n\n   >  export EDITOR=/usr/bin/vi')
        sys.exit(0)
    os.system('%s %s' % (editor, filename))


@click.group()
def cli():
    """Bonfire application management"""
    pass


@click.command()
def config():
    """Configure Bonfire."""
    edit_file(config_file_path())


@click.command()
@click.option('--destination_file', prompt=True)
def copyconfig(destination_file):
    """Copy internal config to external file."""
    cf = config_file_path()
    if os.path.isdir(destination_file):
        destination_file = os.path.join(destination_file,
            os.path.basename(cf))
    if os.path.exists(destination_file):
        yn = raw_input('Overwrite existing file %s? (y/N)' % destination_file)
        if not yn.lower().startswith('y'):
            return
    try:
        shutil.copy2(cf, destination_file)
        click.echo('\nBe sure to set the BONFIRE_CONFIG environment variable:')
        click.echo('\n $ export BONFIRE_CONFIG=%s' % destination_file)
    except IOError:
        click.echo('Could not copy configuration file to destination: %s' % (
            destination_file))
        click.echo('\nBe sure you have proper write permissions, or use:')
        click.echo('\n $ sudo bonfire copyconfig\n')
    

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


cli.add_command(config)
cli.add_command(copyconfig)
cli.add_command(universes)
cli.add_command(build)

