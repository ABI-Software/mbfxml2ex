
MBF XML 2 Ex
============

This program converts MBF XML to Ex format suitable for CMLibs-Zinc.


Install
-------

::

  pip install mbfxml2ex

Usage
-----

::

  mbfxml2exconverter /path/to/input.xml

For more information use the help::

  mbfxml2exconverter --help

Developing
----------

When developing install the required packages for running the tests with::

  pip install .[test]

Then run the tests with::

  python -m unittest discover -s tests

from the repository root directory.

To see the coverage statistics for the package run::

  coverage run --source=mbfxml2ex -m unittest discover -s tests

For a nice HTML rendering of the coverage statistics run::

  coverage html -d html.cover

To view the HTML coverage output::

  python -m http.server 9432 -d html.cover

Then, in a web browser navigate to http://localhost:9432
