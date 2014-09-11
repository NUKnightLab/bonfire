Deployment
==========

Within the cloned repo, run:

::

    pip install .

This will install the bonfire command line tool and dependencies.


Elasticsearch
=============

For information about installing Elasticsearch, please go to http://elasticsearch.org.

Configuration
=============

Bonfire comes with some example universes built-in. To see the configuration, and add your own universe configuration, run ``bonfire config``. You will need to have your EDITOR environment variable set for this command to work.

Each universe defined by a ``[universe:<universe-name>]`` section in the configuration file should have its own Twitter application credentials set for ``twitter_consumer_key``, ``twitter_consumer_secret``, ``twitter_access_token``, and ``twitter_access_token_secret``. To setup your Twitter applications, login to the Twitter developer console with your Twitter account at https://dev.twitter.com/.


Development
===========

To create an editable local deployment for development (ideally within
a virtualenvironment):

::

    pip install --editable .

This will install the bonfire command line tool, and dependencies.


Testing
=======

To run all tests:

::

    python setup.py test

To test a specific module:

::

    python -m unittest tests.test_universe


Logging
=======

Parameters in the [logging] section of the bonfire configuration file are passed to a basicConfig logging configuration. These include

 * filename
 * level
 * filemode
 * format
 * datefmt

If the [logging] section includes an option called ``configfile``, the specified file will be used to setup a fileConfig instead of the basic config. Remaining parameters listed above will be passed to fileConfig as defaults. An example logging config file is provided called ``logging.conf.example``.

Flask Web Application
=====================

There is an example web application in bonfire/web/flaskapp. To run this you will need to install Flask: ``pip install flask``.


