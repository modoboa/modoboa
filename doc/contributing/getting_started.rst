###############
Getting started
###############

You would like to work on Modoboa but you don't know where to start?
You're at the right place! Browse this page to learn useful tips.

With Docker
===========

A docker image is available for developers. To use it, you must
install `docker <https://docs.docker.com/install/>`_ and
`docker-compose <https://docs.docker.com/compose/install/>`_ first.

If not already done, clone the repo and open it::

  $ git clone https://github.com/modoboa/modoboa.git
  $ cd modoboa

Then, just run the following command::

  $ docker-compose up

Then if not done already, run this command to create an OIDC application
in order to be able to log in from the frontend:

..  sourcecode:: bash

  $ docker exec modoboa-api '/bin/sh -c python3 /code/test_project/manage.py createapplication --name frontend --client-id "LVQbfIIX3khWR3nDvix1u9yEGHZUxcx53bhJ7FlD" --user 1 --algorithm RS256 --redirect-uris 'https://localhost:3000/login/logged' public authorization-code'
  $ docker exec modoboa-api '/bin/sh -c python3 /code/test_project/manage.py createapplication --name Dovecot --skip-authorization --client-id=dovecot --client-secret=Toto12345 confidential client-credentials'

It will start the docker environment and make a Modoboa instance
available at ``https://localhost:8000`` and the new admin interface at ``https://localhost:3000``.

If you don't want to use docker or need a more complex development
setup, go to the next section.

Without Docker
==============

Prepare a virtual environment
-----------------------------

A `virtual environment
<https://docs.python.org/fr/3/library/venv.html>`_ is a good way to
setup a development environment on your machine.

To do so, run the following commands::

  $ python3 -m venv <path>
  $ source <path>/bin/activate
  $ git clone https://github.com/modoboa/modoboa.git
  $ cd modoboa
  $ pip install -e .
  $ pip install -r dev-requirements.txt

This will create a symbolic link to your local copy so
any modification you make will be automatically available in your
environment, no need to copy them.

Deploy an instance for development
----------------------------------

.. warning::

   Make sure to :ref:`create a database <database>` before running
   this step. The format of the database url is also described in this
   page.

Now that you have setup a development environment, you can deploy a
test instance and run it::

  $ cd <path>
  $ modoboa-admin.py deploy --dburl default:<database url> --domain localhost --devel instance
  $ python manage.py runserver

You're ready to go! You should be able to access Modoboa at
``http://localhost:8000`` using ``admin:password`` as credentials.

Frontend
========

Legacy interface
----------------

The Django templates and views are used to render this interface, which
is served by the uWSGI application - or the local server in development.
`bower <http://bower.io/>`_  is used to manage the CSS and JavaScript
dependencies - i.e. Boostrap, jQuery - thanks to `django-bower
<https://github.com/nvbn/django-bower>`_.

Those dependencies are listed in a file called :file:`dev_settings.py`
located inside the :file:`<path_to_local_copy>/modoboa/core`
directory.

If you want to add a new dependency, just complete the
``BOWER_INSTALLED_APPS`` parameter and run the following command::

  $ python manage.py bower install

It will download and store the required files into the
:file:`<path_to_local_copy>/modoboa/bower_components` directory.

.. note::
  Don't forget to regenerate the localization files when you add strings. See :ref:`the translation page <translation>`

New Vue.js interface
--------------------

The 2.0 version of Modoboa introduces a completely new interface written
with the `Vue.js <https://vuejs.org/>`_ framework. The source files are
located in the :file:`frontend/` directory.

To set it up, you will need to install NodeJS and Yarn - to manage the
dependencies. Then, navigate to the :file:`frontend/` directory and run::

  $ yarn install

You can now build it and serve it - while running your instance too to
serve the API - with::

  $ yarn serve

Tests
=====

If you deployed an instance for development, you can launch the tests
from it with::

  $ python manage.py test modoboa

You could also test just some them, i.e.::

  $ python manage.py test modoboa.core.tests.test_authentication

Alternatively, you can use `tox <https://tox.readthedocs.io>`_ from
the repository to run all the tests and check the coverage with::

  $ tox

You could limit the environment to a specific Python version with the
``-e py<version>`` argument.

Note that it is also possible to quickly run a test instance without
any deployment - e.g. to preview some changes - by running::

  $ tox -e serve

Documentation
=============

The source files are located in the file:`doc/` folder and are written
in reStructuredText (reST). They are formatted in HTML and compiled
thanks to `Sphinx <https://www.sphinx-doc.org/en/master/>`_.

To build it and see the result, run::

  $ tox -e doc
  $ open .tox/doc/tmp/html/index.html

FAQ
===

bower command is missing in manage.py
-------------------------------------

*bower* command is missing in *manage.py* if you don't use the
``--devel`` option of the ``modoboa-admin.py deploy`` command.

To fix it, regenerate your instance or update your ``settings.py``
file manually. Look at ``devmode`` in
https://github.com/tonioo/modoboa/blob/master/modoboa/core/commands/templates/settings.py.tpl
