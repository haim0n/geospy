======
geospy
======


.. image:: https://img.shields.io/pypi/v/geospy.svg
        :target: https://pypi.python.org/pypi/geospy

.. image:: https://img.shields.io/travis/haim0n/geospy.svg
        :target: https://travis-ci.org/haim0n/geospy

.. image:: https://readthedocs.org/projects/geospy/badge/?version=latest
        :target: https://geospy.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status

.. image:: https://pyup.io/repos/github/haim0n/geospy/shield.svg
     :target: https://pyup.io/repos/github/haim0n/geospy/
     :alt: Updates



Turn you Raspberry Pi to a Mobile GPS.

* Free software: MIT license
* Documentation: https://geospy.readthedocs.io.

Installation
------------
* Install pip::

    sudo apt-get install -y python-pip

* Clone the repo::

    git clone https://github.com/haim0n/geospy.git

* Install the package dependencies::

    sudo apt-get install -y gpsd gpsd-clients python-gps

* Install the package::

    cd geospy; sudo python setup.py install

Getting Started
---------------

What You'll Need
================
* 1 Raspberry Pi (duh)
* [optional]: USB gps device like `this one <http://catb.org/gpsd/hardware.html>`_
* [optional]: WiFi module or dongle
    * In case you choose the WiFi module, you'll need the Pi to be connected to the internet.

Setting the API key
===================
* Refer to `Google maps API howto <https://developers.google.com/maps/documentation/javascript/get-api-key>`_ to get your API key from Google.

* Providing it to geospy could be done by either:
    * `export GOOGLE_API_KEY=value`
    * `geospy --api-key value`

Other knobs and switches
========================
Refer to the utility's help::

    usage: geospy.py [-h] [-V] [-Z] [-O {csv,maps}] [-K API_KEY]

    Location services

    optional arguments:
      -h, --help            show this help message and exit
      -V, --verbose
      -Z, --purge-db        purge all local data
      -O {csv,maps}, --output-db {csv,maps}
                            output db format
      -K API_KEY, --api-key API_KEY
                            set api key



Examples
--------
* Start getting locations::

    $ sudo geospy --api-key 123

* Generate google map of the location history to out.html::

    $ sudo geospy --api-key 123 -O maps

* Erase all location history::

    $ sudo geospy -Z

