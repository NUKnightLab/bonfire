.. Bonfire documentation master file, created by
   sphinx-quickstart on Thu Jul 31 15:06:44 2014.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Bonfire documentation
===================================

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

