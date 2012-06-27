#############################
Migrating from other software
#############################

************
PostfixAdmin
************

Since version 0.8.5, Modoboa provides a simple script to migrate an
existing `PostfixAdmin (version 2.3.3+)
<http://postfixadmin.sourceforge.net/>`_ database to a Modoboa one.

.. note::
   This script is only suitable for a new installation.

First, you must follow the :ref:`installation` step to create a fresh
Modoboa database.

Once done, edit the *setting.py* file. First, add a new database
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

You are now ready to start the migration. Enter Modoboa's root
directory and execute the following command::

  $ PYTHONPATH=$PWD/.. DJANGO_SETTINGS_MODULE=modoboa.settings \
      ./tools/pfxadmin_migrate/migrate.py -r -p <directory that stores mailboxes>

Depending on how many domains/mailboxes your existing setup contains,
the migration can be long. Just wait for the script's ending.

Once the migration has succeed, go the *Admin > Configuration* panel,
click on the *admin* row and modify the value of ``MAILDIR_ROOT`` as
follow::

  MAILDIR_ROOT =

The corresponding field must be empty. Don't touch other fields except
``PASSWORD_SCHEME``, if needed. (set it to the same method as the one
used by PostfixAdmin, check its configuration file if you're not sure)

Click on the *Save* button.

The procedure is over, edit the *settings.py* file and:

* remove the ``pfxadmin`` database connection from the ``DATABASES``
  variable
* remove the ``'modoboa.tools.pfxadmin_migrate',`` from the
  ``INSTALLED_APPS`` variable

You should be able to connect to Modoboa using the same credentials
you were using to connect to PostfixAdmin.
