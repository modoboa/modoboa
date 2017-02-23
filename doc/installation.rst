############
Installation
############

Recommended way
===============

If you start from scratch and want to deploy a complete mail server,
you will love the `modoboa installer
<https://github.com/modoboa/modoboa-installer>`_! It is the easiest
and the quickest way to setup a fully functional server (modoboa,
postfix, dovecot, amavis and more) on one machine.

.. warning::

   For now, only Debian and CentOS based Linux distributions are
   supported. We do our best to improve compatibility but if you use
   another Linux or a UNIX system, you will have to install Modoboa
   :ref:`manually <by_hand>`.

To use it, just run the following commands in your terminal:

.. sourcecode:: bash        

  > git clone https://github.com/modoboa/modoboa-installer
  > cd modoboa-installer
  > sudo ./run.py <mail server hostname>

Wait a few minutes and you're done \o/

.. _by_hand:

Manual installation
===================

For those who need a manual installation or who just want to setup a
specific part, here are the steps you must follow:

.. toctree::
   :maxdepth: 1

   manual_installation/modoboa
   manual_installation/webserver
   manual_installation/dovecot
   manual_installation/postfix

Extensions
----------

Only few commands are needed to add a new extension to your setup.

In case you use a dedicated user and/or a virtualenv, do not forget to
use them:

.. sourcecode:: bash

   > sudo -u <modoboa_user> -i
   > source <virtuenv_path>/bin/activate

Then, run the following commands:

.. sourcecode:: bash

   > pip install <EXTENSION>==<VERSION>
   > cd <modoboa_instance_dir>
   > python manage.py migrate
   > python manage.py collectstatic

Then, restart your web sever.
