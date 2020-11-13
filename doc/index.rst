.. Modoboa documentation master file, created by
   sphinx-quickstart on Mon Jan  3 22:29:25 2011.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Modoboa documentation
=====================

.. image:: _static/modoboa_logo.png
   :align: center

Overview
--------

Modoboa is a mail hosting and management platform including a modern
and simplified Web User Interface designed to work with `Postfix
<http://www.postfix.org>`_ and `Dovecot <http://www.dovecot.org>`_.

It is extensible by nature and comes with a lot of additional extensions:

+---------------------------------------------------------+-------------------------+------------------------------------------------------+
|Name                                                     |Description              |Documentation                                         |
|                                                         |                         |                                                      |
|                                                         |                         |                                                      |
|                                                         |                         |                                                      |
+=========================================================+=========================+======================================================+
|`modoboa-amavis                                          |A frontend for `Amavis   |https://modoboa-amavis.readthedocs.io                 |
|<https://github.com/modoboa/modoboa-amavis>`_            |<http://www.amavis.org>`_|                                                      |
|                                                         |                         |                                                      |
|                                                         |                         |                                                      |
+---------------------------------------------------------+-------------------------+------------------------------------------------------+
|`modoboa-dmarc                                           |A set of tools to use    |https://github.com/modoboa/modoboa-dmarc              |
|<https://github.com/modoboa/modoboa-dmarc>`_             |`DMARC                   |                                                      |
|                                                         |<https://dmarc.org>`_    |                                                      |
+---------------------------------------------------------+-------------------------+------------------------------------------------------+
|`modoboa-imap-migration                                  |Migrate mailboxes from an|https://github.com/modoboa/modoboa-imap-migration     |
|<https://github.com/modoboa/modoboa-imap-migration>`_    |existing server using    |                                                      |
|                                                         |IMAP (and offlineimap)   |                                                      |
+---------------------------------------------------------+-------------------------+------------------------------------------------------+
|`modoboa-pdfcredentials                                  |Generate PDF documents   |https://github.com/modoboa/modoboa-pdfcredentials     |
|<https://github.com/modoboa/modoboa-pdfcredentials>`_    |containing account       |                                                      |
|                                                         |credentials              |                                                      |
+---------------------------------------------------------+-------------------------+------------------------------------------------------+
|`modoboa-pfxadmin-migrate                                |A tool to migrate from   |https://github.com/modoboa/modoboa-pfxadmin-migrate   |
|<https://github.com/modoboa/modoboa-pfxadmin-migrate>`_  |Postfixadmin             |                                                      |
+---------------------------------------------------------+-------------------------+------------------------------------------------------+
|`modoboa-postfix-autoreply                               |Away message editor      |https://modoboa-postfix-autoreply.readthedocs.io      |
|<https://github.com/modoboa/modoboa-postfix-autoreply>`_ |(postfix compatible)     |                                                      |
+---------------------------------------------------------+-------------------------+------------------------------------------------------+
|`modoboa-radicale                                        |A frontend for `Radicale |https://modoboa-radicale.readthedocs.io               |
|<https://github.com/modoboa/modoboa-radicale>`_          |<http://radicale.org>`_  |                                                      |
+---------------------------------------------------------+-------------------------+------------------------------------------------------+
|`modoboa-sievefilters                                    |A Sieve filters (rules)  |https://modoboa-sievefilters.readthedocs.io           |
|<https://github.com/modoboa/modoboa-sievefilters>`_      |editor                   |                                                      |
+---------------------------------------------------------+-------------------------+------------------------------------------------------+
|`modoboa-webmail                                         |A simple webmail         |https://modoboa-webmail.readthedocs.io                |
|<https://github.com/modoboa/modoboa-webmail>`_           |                         |                                                      |
+---------------------------------------------------------+-------------------------+------------------------------------------------------+

Table of contents
-----------------

.. toctree::
   :maxdepth: 1

   installation
   upgrade
   configuration
   moving
   rest_api
   contributing
   contributors
