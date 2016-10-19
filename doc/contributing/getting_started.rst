###########
Useful tips
###########

You would like to work on Modoboa but you don't know where to start?
You're at the right place! Browse this page to learn useful tips.

.. _venv_for_dev:

Prepare a virtual environment
=============================

A `virtual environment
<http://virtualenv.readthedocs.org/en/latest/>`_ is a good way to
setup a development environment on your machine.

.. note::

   ``virtualenv`` is available on all major distributions, just
   install it using your favorite packages manager.

To do so, run the following commands::

  $ virtualenv <path>
  $ source <path>/bin/activate
  $ git clone https://github.com/tonioo/modoboa.git
  $ cd modoboa
  $ python setup.py develop

The ``develop`` command creates a symbolic link to your local copy so
any modification you make will be automatically available in your
environment, no need to copy them.

Deploy an instance for development
==================================

.. warning::

   Make sure to :ref:`create a database <database>` before running
   this step.

Now that you have a :ref:`running environment <venv_for_dev>`, you're
ready to deploy a test instance::

  $ modoboa-admin.py deploy --devel --dburl <database url> <path>
  $ cd <path>
  $ python manage.py runserver

You're ready to go!

Manage static files
===================

Modoboa uses `bower <http://bower.io/>`_ (thanks to `django-bower
<https://github.com/nvbn/django-bower>`_) to manage its CSS and
javascript dependencies.

Those dependencies are listed in a file called :file:`dev_settings.py`
located inside the :file:`<path_to_local_copy>/modoboa/core`
directory.

If you want to add a new dependency, just complete the
``BOWER_INSTALLED_APPS`` parameter and run the following command::

  $ python manage.py bower install

It will download and store the required files into the
:file:`<path_to_local_copy>/modoboa/bower_components` directory.

Test your modifications
=======================

If you deployed a specific instance for your development needs, you
can run the tests suite as follows:

.. sourcecode:: bash

  > python manage.py test modoboa.core modoboa.lib modoboa.admin modoboa.limits modoboa.relaydomains

Otherwise, you can run the tests suite from the repository using `tox
<https://tox.readthedocs.io>`_.

Start a basic Modoboa instance
==============================

From the repository, run the following command to launch a simple
instance with a few fixtures:

.. sourcecode:: bash

  > tox -e serve

You can use admin/password to log in.

Build the documentation
=======================

If you need to modify the documenation and want to see the result, you
can build it as follows:

.. sourcecode:: bash
     
   > tox -e doc
   > firefox .tox/doc/tmp/html/index.html

FAQ
===

bower command is missing in manage.py
-------------------------------------

*bower* command is missing in *manage.py* if you don't use the
``--devel`` option of the ``modoboa-admin.py deploy`` command.

To fix it, regenerate your instance or update your ``settings.py``
file manually. Look at ``devmode`` in
https://github.com/tonioo/modoboa/blob/master/modoboa/core/commands/templates/settings.py.tpl
