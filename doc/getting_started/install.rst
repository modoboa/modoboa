.. _installation:

############
Installation
############

*****************
For the lazy ones
*****************

If you are in a hurry, you will love the `modoboa installer
<https://github.com/modoboa/modoboa-installer>`_! It's a set of Python
scripts to install a fully functional email server on one machine
(modoboa, postfix, dovecot, amavis and more).

To use it, just run the following commands in your terminal::

  $ git clone https://github.com/modoboa/modoboa-installer
  $ cd modoboa-installer
  $ sudo ./run.py <mail server hostname>

Wait a few minutes and you're done \o/

If you have more time or if you are just curious, you can install
Modoboa *the old way* by going to the next section.

************
Requirements
************

* `Python version 2.7+ <http://python.org/>`_
* `Django version 1.7+ <http://docs.djangoproject.com/en/dev/intro/install/#intro-install>`_
* `lxml python module <http://lxml.de/installation.html>`_
* `pycrypto python module <http://www.dlitz.net/software/pycrypto/>`_
* `rrdtool python binding <http://oss.oetiker.ch/rrdtool/>`_
* `sievelib python module <http://pypi.python.org/pypi/sievelib>`_
* `chardet python module <http://pypi.python.org/pypi/chardet>`_
* `argparse python module <http://pypi.python.org/pypi/argparse>`_
* `reversion python module <https://github.com/etianen/django-reversion>`_

.. _get_modoboa:

***********
Get Modoboa
***********

You can choose between two options:

* Use the Python package available on the `PyPI <http://pypi.python.org/pypi>`_
* Download the sources tarball

The easiest one is to install it from PyPI. Just run the following
command and you're done::

  $ pip install modoboa

If you prefer to use the tarball, download the latest one and run the
following procedure::

  $ tar xzf modoboa-<version>.tar.gz
  $ cd modoboa-<version>
  $ python setup.py install

All dependencies will be installed regardless the way you chose. The
only exception concerns the RRDtool binding because there isn't any
python package available, it is directly provided with the official
tarball.

Fortunately, all major distributions include a ready-to-use
package. On Debian/Ubuntu::

  $ apt-get install libcairo2-dev libpango1.0-dev librrd-dev
  $ apt-get install python-rrdtool

`virtualenv <http://www.virtualenv.org/en/latest/>`_ users
==========================================================

When you deploy an application using virtualenv, you may have to
compile some dependencies. For example, modoboa relies on lxml,
which is a C python module. In order to install it, you will need to
install the following requirements:

* python development files
* libxslt development files
* libxml2 development files
* libz development files

On a Debian like system, just run the following command::

  $ apt-get install python-dev libxml2-dev libxslt-dev zlib1g-dev

.. _database:

********
Database
********

Thanks to Django, Modoboa supports several databases. Depending on
the one you will use, you must install the appropriate python package:

* `mysqldb <http://mysql-python.sourceforge.net/>`_ for `MySQL <http://www.mysql.com>`_
* `psycopg2 <http://initd.org/psycopg/>`_ for `PostgreSQL <http://www.postgresql.org>`_

Then, create a user and a database that will be used by Modoboa. Make
sure your database is using UTF8 as a default charset.

.. _deployment:

**********
Deployment
**********

`modoboa-admin.py`, a command line tool, lets you deploy a
*ready-to-use* Modoboa site using only one instruction::

  $ modoboa-admin.py deploy modoboa_example --collectstatic [--dburl default:database-url] [--extensions extensions]

.. note::

   By default, the core application of Modoboa and some necessary plugins
   (admin, relaydomains and limits) are installed. To install extensions,
   use the ``--extensions`` option which accepts a list of extension names
   as argument (``--extensions ext1 ext2 ...``).
   If you want to install all extensions, just use the ``all``
   shortcut like this ``--extensions all``.

   If you choose to install extensions one at a time, you will have to
   add their names in settings.py to ``MODOBOA_APPS``. Also ensure that
   you have the line ``from modoboa_amavis.settings import *`` at the
   end of this file.

   The list of available plugins can be found on the :doc:`index page
   <../index>`. Instructions to install them are available on each plugin page.

.. note::

   You can specify more than one database connection using the
   ``--dburl`` option. Multiple connections are differentiated by a
   prefix. The primary connection must use the ``default:`` prefix (as
   shown in the example above). For the `amavis extension
   <http://modoboa-amavis.readthedocs.org>`_ extension, use the
   ``amavis:`` prefix. An example two connections: ``--dburl
   default:<database url> amavis:<database url>``.

   Your database url should meet the following syntax
   ``scheme://[user:pass@][host:port]/dbname`` **OR**
   ``sqlite:////full/path/to/your/database/file.sqlite``.

   Available schemes are:

   * postgres
   * postgresql
   * postgis
   * mysql
   * mysql2
   * sqlite

The command will ask you a few questions, answer them and you're
done. You can now go to the :ref:`first_use` section.

In case you need a **silent installation** (e.g. if you're using
Salt-Stack, Ansible or whatever), it's possible to supply the database
credentials as commandline arguments.

You can see the complete option list by running the following command::

  $ modoboa-admin.py help deploy

.. note::

  If you plan to serve Modoboa using a URL prefix, you must change the
  value of the ``LOGIN_URL`` parameter to ``LOGIN_URL = '/<prefix>/accounts/login/'``.

.. _first_use:

*********
First use
*********

Your installation should now have a default super administrator:

* Username: ``admin``
* Password: ``password``

It is **strongly** recommended to change this password the first time
you log into Modoboa.

To check if your installation works, just launch the embedded HTTP
server::

  $ python manage.py runserver

You should be able to access Modoboa at http://localhost:8000/.

For a fully working interface using the embedded HTTP server, you need
to set the ``DEBUG`` parameter in settings.py to ``True``.

For a production environment, we recommend using a stable webserver
like :ref:`apache2` or :ref:`nginx-label`. Don't forget to set
``DEBUG`` back to ``False``.
