.. _modoboa_manual_install:

#######
Modoboa
#######

This section describes the installation of the web interface (a
`Django <https://www.djangoproject.com/>`_ project).

This proposed configuration is the one you can find with modoboa-installer. For up to date configuration, `take a look here <https://github.com/modoboa/modoboa-installer/tree/master/modoboa_installer/scripts/files/modoboa/>`_


Prepare the system
------------------

First of all, we recommend the following context:

* A dedicated system user
* A `virtual environment
  <https://packaging.python.org/tutorials/installing-packages/#creating-virtual-environments>`_
  to install the application because it will isolate it (and its
  dependencies) from the rest of your system

The following example illustrates how to realize this on Debian-based
distributions using `virtualenv <https://virtualenv.pypa.io/en/stable/>`_:

.. code-block:: console

   # apt-get install virtualenv python3-pip
   # useradd modoboa  # create a dedicated user
   # sudo -u modoboa -i bash    # log in as the newly created user
   $ virtualenv --python python3 ./env  # create the virtual environment
   $ source ./env/bin/activate          # activate the virtual environment

Modoboa depends on external tools and some of them require compilation
so you need a compiler and a few C libraries. Make sure to install the
following system packages according to your distribution:

+-------------------------------+
| Debian / Ubuntu               |
+===============================+
| build-essential python3-dev   |
| libxml2-dev libxslt-dev       |
| libjpeg-dev librrd-dev        |
| rrdtool libffi-dev libssl-dev |
| pkg-config libcairo2-dev      |
+-------------------------------+

+-----------------------------+
| CentOS                      |
+=============================+
| gcc gcc-c++ python3-devel   |
| libxml2-devel libxslt-devel |
| libjpeg-turbo-devel         |
| rrdtool-devel rrdtool       |
| libffi-devel                |
+-----------------------------+

.. note::

   Alternatively, you could rely on your distribution packages for the Modoboa
   dependencies which require compilation - e.g. ``rrdtool`` - if the version
   is compatible. In this case, you have to create your virtual environment
   with the ``--system-site-packages`` option, and the required system
   packages will be:

    +---------------------------------------+
    | python3-wheel python3-rrdtool rrdtool |
    +---------------------------------------+

Then, install Modoboa by running:

.. code-block:: console

   (env)$ pip install modoboa

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
two ones are described. You should also read the notes for those database
backends on the `official Django documentation
<https://docs.djangoproject.com/en/stable/ref/databases/>`_.

PostgreSQL
**********

Install the corresponding Python binding:

.. code-block:: console

   (env)$ pip install psycopg[binary]>=3.1

.. note::
   Ubuntu and Debian repositories contain python-psycopgX package
   but starting modoboa 2.2.0 minimum version required is 3.1 and
   it has not yet it these distro yet
   Prior modoboa version can run with ``python3-psycopg2``.

Then, create a user and a database. For example, to create the ``modoboa``
database owned by a ``modoboa`` user, run the following commands on your
PostgreSQL server:

.. code-block:: console

   # sudo -l -u postgres createuser --no-createdb modoboa
   # sudo -l -u postgres createdb --owner=modoboa modoboa

MySQL / MariaDB
***************

Install the corresponding Python binding:

.. code-block:: console

   (env)$ pip install mysqlclient

.. note::

   Alternatively, you can install the ``python3-mysqldb`` package instead on
   Debian-based distributions if your virtual environment was created with
   ``--system-site-packages`` option.

.. note::

   MariaDB 10.2 (and newer) require mysqlclient 1.3.11 (or newer).

Then, create a user and a database. For example, to create the ``modoboa``
database owned by a ``modoboa`` user, run the following SQL commands:

.. code-block:: mysql

   CREATE DATABASE modoboa;
   CREATE USER 'modoboa'@'localhost' IDENTIFIED BY 'my-strong-password-here';
   GRANT ALL PRIVILEGES ON modoboa.* TO 'modoboa'@'localhost';

.. _deployment:

Deploy an instance
------------------

``modoboa-admin.py`` is a command line tool that lets you deploy a
*ready-to-use* Modoboa site. To create a new instance into ``./instance``,
you just have to run the following command:

.. code-block:: console

   (env)$ modoboa-admin.py deploy instance --collectstatic \
            --domain <hostname of your server> --dburl default:<database url>

.. note::

   You can install additional extensions during the deploy process. To
   do so, use the ``--extensions`` option which accepts a list of
   names as argument (``--extensions ext1 ext2 ...``). If you want to
   install all extensions, just use the ``all`` keyword like this
   ``--extensions all``.

   If you choose to install extensions one at a time, you will have to
   add their names in settings.py to ``MODOBOA_APPS``. Also ensure that
   you have the line ``from modoboa_amavis.settings import *`` at the
   end of this file and possibly perform more steps. Check the
   documentation/readme of each extensions for specific Instructions.

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

   Fox example, if you were using postgres, you could setup your command like this:
   ``modoboa-admin.py deploy instance_name --collectstatic --domain example.com --dburl default:postgres://user:pass@[localhost]/modoboa``

The command will ask you a few questions, answer them and you're
done.

If you need a **silent installation** (e.g. if you're using
Salt-Stack, Ansible or whatever), it's possible to supply the database
credentials as command line arguments.

You can consult the complete option list by running the following
command:

.. code-block:: console

   (env)$ modoboa-admin.py help deploy

Cron jobs
---------

A few recurring jobs must be configured to make Modoboa works as
expected.

Create a new file, for example :file:`/etc/cron.d/modoboa` and put the
following content inside:

.. sourcecode:: bash

   #
   # Modoboa specific cron jobs
   #
   PYTHON=<path to Python binary inside the virtual environment>
   INSTANCE=<path to Modoboa instance>

   # Operations on mailboxes
   *     *  *  *  *  <mailbox user>    $PYTHON $INSTANCE/manage.py handle_mailbox_operations

   # Generate DKIM keys (they will belong to the user running this job)
   *     *  *  *  *  root     umask 077 && $PYTHON $INSTANCE/manage.py modo manage_dkim_keys

   # Sessions table cleanup
   0     0  *  *  *  root  $PYTHON $INSTANCE/manage.py clearsessions
   # Logs table cleanup
   0     0  *  *  *  root  $PYTHON $INSTANCE/manage.py cleanlogs
   # Logs parsing
   */15  *  *  *  *  root     $PYTHON $INSTANCE/manage.py logparser &> /dev/null
   0     *  *  *  *  modoboa  $PYTHON $INSTANCE/manage.py update_statistics
   # DNSBL checks
   */30  *  *  *  *  modoboa  $PYTHON $INSTANCE/manage.py modo check_mx
   # Public API communication
   0     *  *  *  *  modoboa  $PYTHON $INSTANCE/manage.py communicate_with_public_api

.. hint:: **🥵 potential high load configuration**

   Please note that above crontab might not be ideal on high load systems.
   If you receive a fairly high amount of emails per day, you may want to
   run modoboas logparser tasks *once per night*.

   This has the down side that the statistic graph and message log within
   the UI are updated once per day only.

.. _policy_daemon:

Policy daemon
-------------

Modoboa comes with a built-in `Policy Daemon for Postfix <http://www.postfix.org/SMTPD_POLICY_README.html>`_. Current features are:

* Define daily sending limits for domains and/or accounts

A `redis server <https://redis.io/>`_ is required to run this new daemon.

You can launch it manually using the following command:

.. sourcecode:: bash

   (env)> python manage.py policy_daemon

But we recommend an automatic start using ``systemd`` or
``supervisor``. Here is a configuration example for ``supervisor``:
.. sourcecode:: ini

   [program:policyd]
   autostart=true
   autorestart=true
   command=<path to Python binary inside the virtual environment> <path to Modoboa instance>/manage.py policy_daemon
   directory=<modoboa user home dir>
   redirect_stderr=true
   user=modoboa
   numprocs=1

It will listen by default on ``127.0.0.1`` and port ``9999``. The
policy daemon won't do anything unless you tell :ref:`postfix <policyd_config>` to use it.


RQ daemon
---------

Modoboa uses `RQ <https://python-rq.org>`_ as a job handler for async task.

A `redis server <https://redis.io/>`_ is required to run this new daemon.

A worker needs to be launched in the venv.

You can launch it manually using the following command:

.. sourcecode:: bash

   (env)> rq worker high default low

But we recommend an automatic start using ``systemd`` or
``supervisor``. Here is a configuration example for ``supervisor``:

.. sourcecode:: ini

   [program:modoboa-dkim-worker]
   autostart=true
   autorestart=true
   command=<path to Python binary inside the virtual environment> <path to Modoboa instance>/manage.py rqworker dkim
   directory=<modoboa user home dir>
   user=<opendkim user>
   redirect_stderr=true
   numprocs=1
   stopsignal=TERM


Now you can continue to the :ref:`webserver` section.
