.. Bonfire documentation master file, created by
   sphinx-quickstart on Thu Jul 31 15:06:44 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Welcome to Bonfire's documentation!
===================================

Contents:

.. toctree::
   :maxdepth: 2

Project on Github
=================

The Bonfire project is here: https://github.com/NUKnightLab/bonfire



Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`


Quickstart
==========

The following steps should get you up and running:

 * Be sure you have ElasticSearch intalled and running
 * `git clone git@github.com:NUKnightLab/bonfire.git`
 * Inside the repo: `pip install .`
 * `bonfire config`. Add your Twitter credentials and configure a universe seed of up to 14 users.
 * `bonfire build`. This will expand the universe from the seed and prepare Elasticsearch to run bonfire.
 * In separate terminals run: `bonfire collect` and `bonfire process` for each universe you've defined.
 * To see results in the example web application, be sure to `pip install Flask` and run `app.py` that is located in the repository in web/flaskapp.

# Deployment

Within the cloned repo, run:

```
pip install .
```

This will install the bonfire command line tool and dependencies.


Elasticsearch
=============

For information about installing Elasticsearch, please go to http://elasticsearch.org.

Configuration
=============

Bonfire comes with some example universes built-in. To see the configuration, and add your own universe configuration, run `bonfire config`. You will need to have your EDITOR environment variable set for this command to work.

Each universe defined by a `[universe:<universe-name>]` section in the configuration file should have its own Twitter application credentials set for `twitter_consumer_key`, `twitter_consumer_secret`, `twitter_access_token`, and `twitter_access_token_secret`. To setup your Twitter applications, login to the Twitter developer console with your Twitter account at https://dev.twitter.com/.


Development
===========

To create an editable local deployment for development (ideally within
a virtualenvironment):

```
pip install --editable .
```

This will install the bonfire command line tool, and dependencies.


Testing
=======

To run all tests:

    python setup.py test

To test a specific module:

    python -m unittest tests.test_universe

Usage
=====

The installation and development installation processes above install the bonfire command line utility to your path. For info on using Bonfire, type:

```
bonfire --help
```

Logging
=======

Parameters in the [logging] section of the bonfire configuration file are passed to a basicConfig logging configuration. These include

 * filename
 * level
 * filemode
 * format
 * datefmt

If the [logging] section includes an option called `configfile`, the specified file will be used to setup a fileConfig instead of the basic config. Remaining parameters listed above will be passed to fileConfig as defaults. An example logging config file is provided called `logging.conf.example`.

Flask Web Application
=====================

There is an example web application in bonfire/web/flaskapp. To run this you will need to install Flask: `pip install flask`.


API Documentation
=================

bonfire.cli
-----------
.. automodule:: bonfire.cli
    :members:
    :undoc-members:
    :inherited-members:
    :imported-members:
    :exclude-members: Command

bonfire.config
--------------
.. automodule:: bonfire.config
    :members:
    :undoc-members:
    :inherited-members:

bonfire.content
---------------
.. automodule:: bonfire.content
    :members:
    :undoc-members:
    :inherited-members:

bonfire.dates
-------------
.. automodule:: bonfire.dates
    :members:
    :undoc-members:
    :inherited-members:

bonfire.db
----------
.. automodule:: bonfire.db
    :members:
    :undoc-members:
    :inherited-members:

bonfire.elastic
---------------
.. automodule:: bonfire.elastic
    :members:
    :undoc-members:
    :inherited-members:

bonfire.extract
---------------
.. automodule:: bonfire.extract
    :members:
    :undoc-members:
    :inherited-members:

bonfire.mappings
----------------
.. automodule:: bonfire.mappings
    :members:
    :undoc-members:
    :inherited-members:

bonfire.process
---------------
.. automodule:: bonfire.process
    :members:
    :undoc-members:
    :inherited-members:

bonfire.twitter
---------------
.. automodule:: bonfire.twitter
    :members:
    :undoc-members:
    :inherited-members:

bonfire.universe
----------------
.. automodule:: bonfire.universe
    :members:
    :undoc-members:
    :inherited-members:

