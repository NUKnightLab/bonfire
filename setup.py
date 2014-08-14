"""
Install with `pip install .`

Installs bonfire commands. Writes bonfire.cfg config file to home directory.
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
        #'newspaper',
        'birdy',
        'elasticsearch',
    ],
    data_files=[(expanduser('~'), ['bonfire.cfg'])],
    entry_points="""
        [console_scripts]
        bonfire=bonfire.cli:cli
    """,
    test_suite='tests',
)
