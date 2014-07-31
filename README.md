# Bonfire

Automated curation of tweeted content from your Twitterverse


This is a complete re-write of the original Bonfire project from Knight Lab, which is a Tweeted content curator inspired by Nieman Lab's Fuego project.

Design goals for this version of Bonfire include:

 * Architectural simplicity. Reduce the number of architectural dependencies to further enable adoption and deployment.
 * Universe separation. Eliminate the sharing of resources between universes to further simplify the architecture and to facilitate scalability.
 * Leverage Elasticsearch. Since Elastic is being used for content search as a core feature, we will leverage this resource for general storage of Tweets, web content, and resolved URL caching. Consideration for utilizing Elastic as a processing queue is also being considered. In the end, Redis may prove to continue to be the better choice here.
 * Abstract content aggregation and search functions to enable Python-based web applications. Non-Python based applications can connect directly to Elasticsearch.

# Deployment

Within the cloned repo, run:

```
pip install .
```

This will install the bonfire command line tool and dependencies.

*Important:* Do not run pip install with the `--upgrade` option unless you have copied your configuration changes to an external location. `pip install --upgrade` will overwrite the current internal configuration.

## Installation errors

Do not ignore pip install errors. If you see something like this:

```
error: command 'gcc' failed with exit status 1
```

The likely culprits are lxml and Pillow, which are both dependencies for Newspaper, a library that Bonfire uses for article extraction from web pages.

For further info on getting lxml installed, go here: http://lxml.de/installation.html#installation

For Pillow installation: http://pillow.readthedocs.org/en/latest/installation.html


## Elasticsearch

For information about installing Elasticsearch, please go to http://elasticsearch.org.

## Configuration

Bonfire comes with some example universes built-in. To see the configuration, and add your own universe configuration, run `bonfire config`. You will need to have your EDITOR environment variable set for this command to work.

Each universe defined by a `[universe:<universe-name>]` section in the configuration file should have its own Twitter application credentials set for `twitter_consumer_key`, `twitter_consumer_secret`, `twitter_access_token`, and `twitter_access_token_secret`. To setup your Twitter applications, login to the Twitter developer console with your Twitter account at https://dev.twitter.com/.

## Externalizing the configuration file

The internal configuration file is provided to get you up-and-running quickly. It is strongly recommended in a real deployment that you externalize the configuration with the `bonfire copyconfig` command. After copying your configuration to an external location, be sure to set the `BONFIRE_CONFIG` environment variable to point to that location.

# Development

To create an editable local deployment for development (ideally within
a virtualenvironment):

```
pip install --editable .
```

This will install the bonfire command line tool, and dependencies.


## Bonfire config

If Bonfire is installed as --editable for local development, setup will not copy the bonfire.cfg file into the environment. Either copy bonfire.cfg from the repo to config/bonfire.cfg relative to your environment root, or to a location specified by the BONFIRE_CONFIG environment variable. If you are making development changes to the repo copy of bonfire.cfg, set BONFIRE_CONFIG to point directly to the repo file.


# Testing

To run all tests:

    python setup.py test

To test a specific module:

    python -m unittest tests.test_universe

# Usage

The installation and development installation processes above install the bonfire command line utility to your path. For info on using Bonfire, type:

```
bonfire --help
```

# Logging
Parameters in the [logging] section of the bonfire configuration file are passed to a basicConfig logging configuration. These include

 * filename
 * level
 * filemode
 * format
 * datefmt

If the [logging] section includes an option called `configfile`, the specified file will be used to setup a fileConfig instead of the basic config. Remaining parameters listed above will be passed to fileConfig as defaults. An example logging config file is provided called `logging.conf.example`.

# Flask Web Application

There is an example web application in bonfire/web/flaskapp. To run this you will need to install Flask: `pip install flask`.
