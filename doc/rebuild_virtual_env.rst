Sometimes when upgrading your Operating System (eg from Ubuntu 17.04
to Ubuntu 17.10) your virtual environment running modoboa can get
corrupted. Your first response will be to panic but fear not! The
solution is in this document.

First things first:

Recover your database password
==============================

You will need to recover your database password (if using mysql or
postgresql). You will find this in ``/etc/postfix/sql-aliases.cf`` or
any file with ``sql-*.cf`` in the ``/etc/postfix`` directory.

Make note of this as you will need it when reconfiguring modoboa.

Reinstall Modoboa
=================

Start out by backup up your modoboa settings file located in the
``modoboa instance`` directory
(``/srv/modoboa/instance/instance/settings.py`` if you used the
default installer configuration). This contains your current
configuration.

Next, you want to remove all current modoboa files.

After doing this, follow the manual installation instructions for :ref:`modoboa_manual_install` **only** as everything should be working properly.

After this completes, simply restore your backed up settings file to
``/srv/instance/instance/settings.py`` (if you used installer default
configuration). You will then need to reinstall your `extensions
<http://modoboa.readthedocs.io/en/latest/index.html>`_.

You can find which plugins you had in your ``settings.py`` file under
the ``MODOBOA_APPS`` variable.

Instructions to install extensions can also be `found here
<http://modoboa.readthedocs.io/en/latest/installation.html#extensions>`_.

Once you have completed this step, you will need to run the following
commands:

.. sourcecode:: bash

   > (env) $ cd <instance_dir>
   > (env) $ python manage.py migrate
   > (env) $ python manage.py collectstatic
  
You will then see a message similar to:

.. sourcecode:: text

  You have requested to collect static files at the destination
  location as specified in your settings:

      /srv/modoboa/instance/sitestatic

  This will overwrite existing files!
  Are you sure you want to do this?

  Type 'yes' to continue, or 'no' to cancel:
  
You will want to answer ``yes`` here then simply restart the ``uwsgi``
process with ``service uwsgi restart`` and you should be up and
running again.

Simply log into your modoboa web panel and verify that your extensions
and webmail box is working.

Information
***********

Rebuild instructions from:
`https://help.pythonanywhere.com/pages/RebuildingVirtualenvs/
<https://help.pythonanywhere.com/pages/RebuildingVirtualenvs/>`_
