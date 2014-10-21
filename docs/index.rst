.. Bonfire documentation master file, created by
   sphinx-quickstart on Thu Jul 31 15:06:44 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

What is Bonfire?
===================================
Bonfire is a toolkit you can use to track link sharing on Twitter. Inspired by Nieman Lab's Fuego_, Bonfire tracks tweets from a *universe* of users, looking for shared URLs. Bonfire can provide simple analytics about the shared URLs (at the moment, the number of times the URL was shared in a given time period), and creates a search index of the shared documents and the text of tweets.

Bonfire also has a simple method for building a universe of thousands of Twitter users based on a small seed list of a dozen or so Twitter handles.

Bonfire is currently in a developer release--running your own instance requires comfort with the command line. Setting it up to continuously monitor Twitter takes some "devops" skills, and at the moment, there is only a rough web interface. 

We welcome ideas, priorities, and pull requests. For now you can use `Github Issues`_ to reach us.


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
 * ``git clone git@github.com:NUKnightLab/bonfire.git``
 * Inside the repo: ``pip install .`` (preferably in a virtualenv)
 * ``bonfire config``. Add your Twitter credentials and configure a universe seed of up to 14 users.
 * ``bonfire build``. This will expand the universe from the seed and prepare Elasticsearch to run bonfire.
 * In separate terminals run: ``bonfire collect`` and ``bonfire process`` for each universe you've defined.
 * To see results in the example web application, be sure to ``pip install Flask`` and run ``app.py`` that is located in the repository in web/flaskapp.


Command-line Usage
==================

The quickstart above will install the bonfire command line utility to your path. For info on using Bonfire, type:

::

    bonfire --help

Documentation Contents
======================

.. toctree::
   :maxdepth: 2

   general
   api

.. _Fuego: http://www.niemanlab.org/fuego/
.. _Github Issues: https://github.com/NUKnightLab/bonfire/issues