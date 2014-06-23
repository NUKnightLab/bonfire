# Bonfire

Automated curation of tweeted content from your Twitterverse


This is a complete re-write of the original Bonfire project from Knight Lab, which is a Tweeted content curator inspired by the Nieman Labs Fuego project.

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

## Elasticsearch Python client library

The Elasticsearch Python client source is available at: https://github.com/elasticsearch/elasticsearch-py. 

## Elasticsearch

For information about installing Elasticsearch, please go to http://elasticsearch.org.

# Development

To create an editable local deployment for development (ideally within
a virtualenvironment):

```
pip install --editable .
```

This will install the bonfire command line tool, and dependencies except for the Elasticsearch Python client.

For development, you should have Elasticsearch (version 1.0.1) running and accessible from your development host.

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
