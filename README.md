# Bonfire

Automated curation of tweeted content from your Twitterverse. A Tweeted content curator inspired by Nieman Lab's Fuego project and developed jointly by Nieman Lab and Knight Lab.

# Documentation

Docs are [here](http://nuknightlab.github.io/bonfire/)

# Quickstart

The following steps should get you up and running:

 * Be sure you have ElasticSearch intalled and running
 * `git clone git@github.com:NUKnightLab/bonfire.git`
 * Inside the repo: `pip install .`
 * `bonfire config`. Add your Twitter credentials and configure a universe seed of up to 14 users.
 * `bonfire build`. This will expand the universe from the seed and prepare Elasticsearch to run bonfire.
 * In separate terminals run: `bonfire collect` and `bonfire process` for each universe you've defined.
 * To see results in the example web application, be sure to `pip install Flask` and run `app.py` that is located in the repository in web/flaskapp.

