.. _modoboa_manual_install:

#######
Modoboa
#######

This section describes the installation of the web interface (a
`Django <https://www.djangoproject.com/>`_ project).

Prepare the system
------------------

First of all, we recommand the following context:

* Use a dedicated system user
* Use a `virtualenv <http://www.virtualenv.org/en/latest/>`_ to
  install the application because it will isolate it (and its
  dependencies) from the rest of your system

The following example illustrates how to realize this (Debian like system):

.. sourcecode:: bash

  > sudo apt-get install python-virtualenv python-pip
  > sudo useradd modoboa
  > sudo -i -u modoboa
  > virtualenv env
  > source env/bin/activate
  (env)> pip install -U pip

Modoboa depends on external tools and some of them require compilation
so you need a compiler and a few C libraries. Make sure to install the
following system packages according to your distribution:

+------------------------------+
|Debian / Ubuntu               |
+==============================+
|build-essential python-dev    |
|libxml2-dev libxslt-dev       |
|libjpeg-dev librrd-dev        |
|rrdtool libffi-dev            |
|                              |
+------------------------------+

+------------------------------+
|CentOS                        |
+==============================+
|gcc gcc-c++ python-devel      |
|libxml2-devel libxslt-devel   |
|libjpeg-turbo-devel           |
|rrdtool-devel rrdtool         |
|libffi-devel                  |
+------------------------------+

Then, install Modoboa:

.. sourcecode:: bash

  (env)> pip install modoboa

.. _database:

Database
--------

.. warning::

   This documentation does not cover the installation of a database
   server but only the setup of a functional database that Modoboa
   will use.

Thanks to Django, Modoboa is compatible with the following databases:

* PostgreSQL
* MySQL / MariaDB
* SQLite

Since the last one does not require particular actions, only the first
two ones are described.

PostgreSQL
**********

Install the corresponding Python binding:

.. sourcecode:: bash

  (env)> pip install psycopg2

Then, create a user and a database:

.. sourcecode:: bash

  > sudo -i -u postgres
  >

MySQL / MariaDB
***************

Install the corresponding Python binding:

.. sourcecode:: bash

  (env)> pip install mysqlclient

.. note::

   MariaDB 10.2 (and newer) require mysqlclient 1.3.11 (or newer).

Then, create a user and a database:

.. sourcecode:: bash

  > mysqladmin -u root -p create modoboa

Deploy an instance
------------------

``modoboa-admin.py``, a command line tool, lets you deploy a
*ready-to-use* Modoboa site using only one instruction::

  (env)> modoboa-admin.py deploy instance --collectstatic \
           --domain <hostname of your server> --dburl default:database-url

.. note::

   You can install additional extensions during the deploy process. To
   do so, use the ``--extensions`` option which accepts a list of
   names as argument (``--extensions ext1 ext2 ...``). If you want to
   install all extensions, just use the ``all`` keyword like this
   ``--extensions all``.

   If you choose to install extensions one at a time, you will have to
   add their names in settings.py to ``MODOBOA_APPS``. Also ensure that
   you have the line ``from modoboa_amavis.settings import *`` at the
   end of this file.

   The list of available extensions can be found on the :doc:`index
   page <../index>`. Instructions to install them are available on
   each extensions page.

.. note::

   You can specify more than one database connection using the
   ``--dburl`` option. Multiple connections are differentiated by a
   prefix.

   The primary connection must use the ``default:`` prefix (as shown
   in the example above). For the `amavis
   <http://modoboa-amavis.readthedocs.org>`_ extension, use the
   ``amavis:`` prefix. For example: ``--dburl
   default:<database url> amavis:<database url>``.

   A database url should meet the following syntax
   ``<mysql|postgres>://[user:pass@][host:port]/dbname`` **OR**
   ``sqlite:////full/path/to/your/database/file.sqlite``.

The command will ask you a few questions, answer them and you're
done.

If you need a **silent installation** (e.g. if you're using
Salt-Stack, Ansible or whatever), it's possible to supply the database
credentials as commandline arguments.

You can consult the complete option list by running the following
command::

  $ modoboa-admin.py help deploy

Cron jobs
---------

A few recurring jobs must be configured to make Modoboa works as
expected.

Create a new file, for example :file:`/etc/cron.d/modoboa` and put the
following content inside::

  #
  # Modoboa specific cron jobs
  #
  PYTHON=<PATH TO PYTHON BINARY>
  INSTANCE=<PATH TO MODOBOA INSTANCE>

  # Operations on mailboxes
  *       *       *       *       *       vmail   $PYTHON $INSTANCE/manage.py handle_mailbox_operations

  # Sessions table cleanup
  0       0       *       *       *       root    $PYTHON $INSTANCE/manage.py clearsessions

  # Logs table cleanup
  0       0       *       *       *       root    $PYTHON $INSTANCE/manage.py cleanlogs

  # Logs parsing
  */5     *       *       *       *       root    $PYTHON $INSTANCE/manage.py logparser &> /dev/null
  0       *       *       *       *       root    $PYTHON $INSTANCE/manage.py update_statistics

  # DNSBL checks
  */30    *       *       *       *       root    $PYTHON $INSTANCE/manage.py modo check_mx

  # Public API communication
  0       *       *       *       *       root    $PYTHON $INSTANCE/manage.py communicate_with_public_api

  # Generate DKIM keys (they will belong to the user running this job)
  *       *       *       *       *       root    umask 077 && $PYTHON $INSTANCE/manage.py modo manage_dkim_keys


Now you can continue to the :ref:`webserver` section.
