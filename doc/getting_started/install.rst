.. _installation:

############
Installation
############

************
Requirements
************

* `Python version 2.6+ <http://python.org/>`_
* `Django version 1.5+ <http://docs.djangoproject.com/en/dev/intro/install/#intro-install>`_
* `south version 0.7+ <http://south.aeracode.org/>`_
* `lxml python module <http://codespeak.net/lxml/>`_
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

The easiest one is to install it from the *PyPI*. Just run the
following command and you're done::

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

When you deploy an application using *virtualenv*, you may have to
compile some dependencies. For example, *modoboa* relies on *lxml*,
which is a C python module. In order to install it, you will need to
install the following requirements:

* python development files
* libxslt development files
* libxml2 development files

On a *Debian* like system, just run the following command::

  $ apt-get install python-dev libxml2-dev libxslt-dev

.. _database:

********
Database
********

Thanks to *django*, Modoboa supports several databases. Depending on
the one you will use, you must install the appropriate python package:

* `mysqldb <http://mysql-python.sourceforge.net/>`_ for `MySQL <http://www.mysql.com>`_
* `psycopg2 <http://initd.org/psycopg/>`_ for `PostgreSQL <http://www.postgresql.org>`_

Then, create a user and a database that will be used by Modoboa. Make
sure your database is using UTF8 as a default charset.

.. _deployment:

**********
Deployment
**********

`modoboa-admin.py`, a command line tool, let you deploy a
*ready-to-use* Modoboa site using only one instruction::

  $ modoboa-admin.py deploy modoboa_example --syncdb --collectstatic [--with-amavis]

Just answer the few questions and you're done. You can now go to the
:ref:`first_use` section.

.. note::

   The `--with-amavis` option must be set only if you intend to use
   the :ref:`amavis_frontend`.

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

You should be able to access Modoboa at http://locahost:8000/.

For a production environnement, we recommend using a stable webserver
like :ref:`apache2` or :ref:`nginx-label`.
