Reference Guide
===============

``mpiws`` Command
-----------------

.. _usage:

Usage
~~~~~

:command:`mpiws [OPTIONS]`

.. _options:

Options
~~~~~~~

.. program: virtualenv

.. option:: -h, --help

   show this help message and exit

.. option:: -c, --config CONF

   Path to configuration file

.. option:: -l LEVEL
  
   Log level for debugging. LEVEL can be one of the following

   DEBUG, INFO, WARNING, ERROR, CRITICAL, VERBOSE

.. option:: -s, --show

   Show current configuration

.. option:: -i, --input

   Path to input (enrollee) file

.. option:: -o, --output

   Serialized MPI/MRN enrollee output

.. option:: -t, --throttle        

   Throttle web service (WSDL) calls

.. option:: -n, --noheader        

   Do not write csv header


.. _Distribute: https://pypi.python.org/pypi/distribute
.. _Setuptools: https://pypi.python.org/pypi/setuptools


.. note::

 Refer the configuration file for detailed description of the parameters and their meaning.
 A brief summary of the parameters are shown in the table below

