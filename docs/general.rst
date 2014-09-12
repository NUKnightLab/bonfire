Installation
============

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


Deployment
==========

It is recommended that you run the bonfire processes via a process manager. The following demonstrates Upstart usage for Ubuntu. 

Upstart
-------

The following example shows use of upstart with bonfire being executed by a user called ``apps`` within a virtual environment at ``/home/apps/env/bonfire``. The virtualenv sets the ``BONFIRE_CONFIG`` environment variable to ``/etc/bonfire.cfg``. The bonfire.cfg file has a logging section that looks like this:

::

    [logging]
    filename=/var/log/bonfire.log
    level=WARNING

/etc/init/bonfire-collect.conf

::

    start on filesystem and net-device-up IFACE=lo

    stop on shutdown

    respawn

    script
      . /home/apps/env/bonfire/bin/activate
      exec bonfire collect journotech
    end script 


/etc/init/bonfire-process.conf

::

    start on filesystem and net-device-up IFACE=lo

    stop on shutdown

    respawn

    script
      . /home/apps/env/bonfire/bin/activate
      exec bonfire process journotech
    end script

You can then control the bonfire services with:

::

    sudo service bonfire-collect [start|stop|restart]


Troublehooting Upstart
----------------------
If your Upstart services seem to be running, but you aren't seeing any Tweets or any logs, be sure to check the upstart logs. E.g: /var/log/upstart/bonfire-collect.log

Troubleshooting the Bonfire collector
-------------------------------------
The Twitter stream can be a bit finicky and the collector has been known stop collecting even when the stream connection remains open. Firstly, be sure to run the collector in a process manager, as described above. Secondly, it might be useful to monitor the raw tweet queue and occasionally restart the collector process if the queue is empty. The following example shows restarting the collector, configured as in the above examples with upstart. This script can be run with cron to periodically check the queue.

/home/apps/sites/bonfire/monitor.py
::

    import subprocess
    from bonfire.db import get_latest_raw_tweet

    def main():
            if get_latest_raw_tweet('journotech'):
                print('bonfire collect queue not empty')
            else:
                print('restarting bonfire collect')
                subprocess.call('service bonfire-collect restart', shell=True)

    if __name__=='__main__':
        main()


/etc/cron.d/bonfire
::

    PYTHONPATH=/home/apps/sites/bonfire
    BONFIRE_CONFIG=/etc/bonfire.cfg

    */15 * * * * root cd /home/apps/sites/bonfire; /home/apps/env/bonfire/bin/python monitor.py  >> /home/apps/log/bonfire/bonfire_monitor.log 2>&1
