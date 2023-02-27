modoboa-dmarc
=============

.. _dmarcdoc:

A set of tools to use DMARC through Modoboa.

This feature is still in BETA stage, for now it only parses XML aggregated
reports and generate visual reports (using c3.js) on a per-domain basis.

Installation
------------

.. note::
    modoboa-installer can automatically set it up for you.

Make sure to install the following additional system package according to your distribution:

+-----------------+
| Debian / Ubuntu |
+=================+
| libmagic1       |
+-----------------+

+------------+
| CentOS     |
+============+
| file-devel |
+------------+


Integration with Postfix
------------------------

A management command is provided to automatically parse DMARC
aggregated reports (rua) and feed the database. The execution of this
command can be automated with the definition of a postfix service and
a custom transport table.

First, declare a new service in ``/etc/postfix/master.cf``::

  dmarc-rua-parser unix  -       n       n       -       -       pipe
    flags= user=vmail:vmail argv=<path to python> <path to modoboa instance>/manage.py import_aggregated_report --pipe

Define a new transport table inside ``/etc/postfix/main.cf``::

  transport_maps =
      hash:/etc/postfix/dmarc_transport
      # other transport maps...

Create a file called ``/etc/postfix/dmarc_transport`` with the following content::

  <email address your declared in your DNS record>  dmarc-rua-parser:

.. note::
    You must not declare this email address as an identity (user account or alias), else DMARC reports will be directed to your mailbox and won't be parsed.

Hash the file using the following command::

  $ postmap /etc/postfix/dmarc_transport

Finally, reload postfix::

  $ service postfix reload
