###############
Getting started
###############

************
Installation
************

Using the installer
===================

If you start from scratch and want to deploy a complete mail server,
you will love the `modoboa installer
<https://github.com/modoboa/modoboa-installer>`_! It is the easiest
and the quickest way to setup a fully functional server (modooba,
postfix, dovecot, amavis and more) on one machine.

.. warning::

   For now, only Debian and CentOS based Linux distributions are
   supported. We do our best to improve compatibility but if you use
   another Linux or a UNIX system, you will have to install Modoboa
   :ref:`by_hand`.

To use it, just run the following commands in your terminal::

  $ git clone https://github.com/modoboa/modoboa-installer
  $ cd modoboa-installer
  $ sudo ./run.py <mail server hostname>

Wait a few minutes and you're done \o/

.. _by_hand:

By hand
=======

In case you already have a running server (postfix, dovecot, etc.) or
you want to build a multi-machine architecture, you can install
Modoboa manually.

Since Modoboa is a web application written in Python, the procedure
can be splitted in two parts: installing the application and
installing a web server.

Modoboa
-------

Prepare the system
~~~~~~~~~~~~~~~~~~

First of all, we recommand the following context:

* using a dedicated system user
* using a `virtualenv <http://www.virtualenv.org/en/latest/>`_ to
  install the application because it will isolate it (and its
  dependencies) from the rest of your system

The following example illustrates how to realize this (Debian like system)::

  > sudo apt-get install python-virtualenv python-pip
  > sudo useradd modoboa
  > sudo -i modoboa
  > virtualenv env
  (env)> source env/bin/activate
  (env)> pip install -U pip

FIXME: dépendances système pour compilation

Then, install Modoboa::

  (env)> pip install modoboa

Database
~~~~~~~~

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

Install the corresponding Python binding::

  (env)> pip install psycopg2

Then, create a user and a database::

  > sudo -i postgres
  >

MySQL / MariaDB
***************

Install the corresponding Python binding::

  (env)> pip install MySQL-Python

Then, create a user and a database::

  > mysqladmin -u root -p create modoboa

Deploy an instance
~~~~~~~~~~~~~~~~~~

`modoboa-admin.py`, a command line tool, lets you deploy a
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
done. You can now go to the :ref:`first_use` section.

In case you need a **silent installation** (e.g. if you're using
Salt-Stack, Ansible or whatever), it's possible to supply the database
credentials as commandline arguments.

You can consult the complete option list by running the following
command::

  $ modoboa-admin.py help deploy


  
*******
Upgrade
*******

.. warning::

   The new version you are going to install may need to modify your
   database. Before you start, make sure to backup everything!

Most of the time, upgrading your installation to a newer Modoboa
version only requires a few actions. In any case, you will need to
apply the general procedure first and then check if the version you
are installing requires specific actions.

.. note::
   
   In case you use a dedicated user and/or a virtualenv, do not forget to
   use them::

     > sudo -i <modoboa_user>
     > source <virtuenv_path>/bin/activate

The general procedure is as follows::

  > pip install modoboa==<VERSION>
  > cd <modoboa_instance_dir>
  > python manage.py migrate
  > python manage.py collectstatic

Once done, check if the version you are installing requires
:ref:`specific_upgrade_instructions`.
  
Finally, restart your web server.
