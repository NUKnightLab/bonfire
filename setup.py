"""
Install with `pip install .`

WARNING: pip install with `--upgrade` option will overwrite the currently
installed internal configuration. It is recommended that you run
`bonfire copyconfig` to externalize your configuration file.
"""
from os.path import expanduser
from setuptools import setup, find_packages 


setup(
    name='bonfire',
    version='0.1',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click',
        'newspaper',
    ],
    data_files=[('config', ['bonfire.cfg'])],
    entry_points="""
        [console_scripts]
        bonfire=bonfire.cli:cli
    """,
    test_suite='tests',
)
