from os.path import expanduser
from setuptools import setup, find_packages 

"""
TODO: will this potially overwrite modified configs? Does setuptools give us
a way to deal with this? Need to preserve internal config if it has
been modified.
"""

setup(
    name='bonfire',
    version='0.1',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Click',
    ],
    data_files=[('config', ['bonfire.cfg'])],
    entry_points="""
        [console_scripts]
        bonfire=bonfire.cli:cli
    """,
    test_suite='tests',
)
