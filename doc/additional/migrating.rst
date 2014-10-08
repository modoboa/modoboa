#############################
Migrating from other software
#############################

************
PostfixAdmin
************

Modoboa provides a simple script to migrate an
existing `PostfixAdmin (version 2.3.3+)
<http://postfixadmin.sourceforge.net/>`_ database to a Modoboa one.

.. note::
   This script is only suitable for a new installation.

First, you must follow the :ref:`installation` step to create a fresh
Modoboa database.

Once done, edit the :file:`settings.py` file. First, add a new database
connection named ``pfxadmin`` into the ``DATABASES`` variable
corresponding to your PostfixAdmin setup::

  DATABASES = {
      "default" : {
          # default connection definition
      },
      "pfxadmin" : {
          "ENGINE" : "<engine>",
          "NAME" : "<database name>",
          "USER" : "<database user>",
          "PASSWORD" : "<user password>",
      }  
  }

This connection should correspond to the one defined in PostfixAdmin's
configuration file.

Then, uncomment the line containing
``'modoboa.tools.pfxadmin_migrate'`` inside the ``MODOBOA_APPS``
variable and save your changes.

You are now ready to start the migration so run the following commands::

  $ cd <modoboa_site>
  $ python manage.py migrate_from_postfixadmin -s <password scheme>

``<password scheme>`` must be replaced by the scheme used within
postfixadmin (``crypt`` most of the time).

Depending on how many domains/mailboxes your existing setup contains,
the migration can be long. Just wait for the script's ending.

The procedure is over, edit the :file:`settings.py` file and:

* remove the ``pfxadmin`` database connection from the ``DATABASES``
  variable
* remove the ``'modoboa.tools.pfxadmin_migrate',`` from the
  ``MODOBOA_APPS`` variable

You should be able to connect to Modoboa using the same credentials
you were using to connect to PostfixAdmin.
