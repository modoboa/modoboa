.. _installation:

############
Installation
############

************
Requirements
************

* `Python version 2.6+ <http://python.org/>`_
* `Django version 1.3+ <http://docs.djangoproject.com/en/dev/intro/install/#intro-install>`_
* `south version 0.7+ <http://south.aeracode.org/>`_
* `lxml python module <http://codespeak.net/lxml/>`_
* `pycrypto python module <http://www.dlitz.net/software/pycrypto/>`_
* `rrdtool python binding <http://oss.oetiker.ch/rrdtool/>`_
* `sievelib python module <http://pypi.python.org/pypi/sievelib>`_

Optional
========

* `ckeditor version 3.4.1+ <http://ckeditor.com/>`_

***********
Get Modoboa
***********

You can choose between two options:

* Use the Python package available on the `PyPI <http://pypi.python.org/pypi>`_
* Download the sources tarball

The easiest one is to install it from the *PyPI*. Just run the
following command and you're done::

  $ pip install modoboa

If you prefer to use the tarball, download the latest one and run the
following procedure::

  $ tar xzf modoboa-<version>.tar.gz
  $ cd modoboa-<version>
  $ python setup.py install

.. _database:

********
Database
********

Thanks to *django*, Modoboa supports several databases. Depending on
the one you will use, you must install the appropriate python package:

* `MySQL <http://www.mysql.com>`_: `mysqldb <http://mysql-python.sourceforge.net/>`_
* `PostgreSQL <http://www.postgresql.org>`_ : `psycopg2 <http://initd.org/psycopg/>`_
* `SQLite <http://www.sqlite.org>`_: already shipped with *Python*

Then, create a user and a database that will be used by Modoboa. Make
sure your database is using UTF8 as a default charset.

**********
Deployment
**********

As Modoboa is a set of Django applications, you need to create a new
project. Just run the following commands::

  $ cd /var/www
  $ django-admin.py startproject modoboa_example
  $ cd modoboa_example
  $ wget http://modoboa.org/resources/settings.py
  $ wget http://modoboa.org/resources/urls.py
  $ mkdir media

Then, edit the freshly downloaded *settings.py* file and adjust the
database relative information. (see :ref:`database`).

.. note::

  If you plan to serve Modoboa using a URL prefix, you must change the
  value of the ``LOGIN_URL`` parameter to ``LOGIN_URL = '/<prefix>/accounts/login/'``.

Finally, run the following commands::

  $ python manage.py collectstatic
  $ python manage.py syncdb --migrate --noinput

At the end of this command, a default super administrator is
available:

* Username: ``admin``
* Password: ``password``

It is **strongly** recommanded to change this password the first time
you log into Modoboa.
