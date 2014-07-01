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

This will install the bonfire command line tool and dependencies except for the Elasticsearch database and the Elasticsearch Python client library.

*Important:* Do not run pip install with the `--upgrade` option unless you have copied your configuration changes to an external location. `pip install --upgrade` will overwrite the current internal configuration.

## Elasticsearch Python client library

The Elasticsearch Python client source is available at: https://github.com/elasticsearch/elasticsearch-py. This needs to be installed separately.

## Elasticsearch

For information about installing Elasticsearch, please go to http://elasticsearch.org.

## Configuration

Bonfire comes with some example universes built-in. To see the configuration, and add your own universe configuration, run `bonfire config`. You will need to have your EDITOR environment variable set for this command to work.

Each universe defined by a `[universe:<universe-name>]` section in the configuration file should have its own Twitter application credentials set for `twitter\_consumer\_key`, `twitter\_consumer\_secret`, `twitter\_access\_token`, and `twitter\_access\_token\_secret`. To setup your Twitter applications, login to the Twitter developer console with your Twitter account at https://dev.twitter.com/.

## Externalizing the configuration file

The internal configuration file is provided to get you up-and-running quickly. It is strongly recommended in a real deployment that you externalize the configuration with the `bonfire copyconfig` command. After copying your configuration to an external location, be sure to set the `BONFIRE\_CONFIG` environment variable to point to that location.

# Development

To create an editable local deployment for development (ideally within
a virtualenvironment):

```
pip install --editable .
```

This will install the bonfire command line tool, and dependencies except for the Elasticsearch Python client, and the bonfire.cfg config file setup.

## Elasticsearch client

For development, you should have Elasticsearch (version 1.0.1) running and accessible from your development host.

## Bonfire config

If Bonfire is installed as --editable for local development, setup will not copy the bonfire.cfg file into the environment. Either copy bonfire.cfg from the repo to config/bonfire.cfg relative to your environment root, or to a location specified by the BONFIRE_CONFIG environment variable. If you are making development changes to the repo copy of bonfire.cfg, set BONFIRE_CONFIG to point directly to the repo file.


## Elasticsearch client

We are currently using the Elasticsearch Python client version 1.0.1 which is not available in PyPi. Install from source by running python setup.py. The Elasticsearch Python client source is available at: https://github.com/elasticsearch/elasticsearch-py. 

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
