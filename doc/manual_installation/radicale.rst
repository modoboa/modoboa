.. _radicale:

#######
Radicale
#######

This page is displaying how to install and use radicale when either having installed modoboa manually or with the dedicated installer.

.. _radicale_oauth2:

OAuth 2 authentication
======================

..  note::

  These steps are automatic if you use an up-to-date modoboa-installer to install/upgrade.

Preparing the usage of radicale (manual install only)
-----------------------------------------------------

It is assumed you have not installed in the past radicale from your package manager and your modoboa installation is working correctly. If so, you may skip this section and proceed to the next one.
You will need to create directories for the radicale user, needed files and set-up the account (location may change depending on your OS and initial set-up).

.. sourcecode:: bash

  > sudo mkdir /var/lib/radicale /etc/radicale
  > sudo touch /etc/radicale/{rights,config}
  > sudo adduser --system --home /var/lib/radicale/ --no-create-home --gecos "Radicale CalDAV server" --group --disabled-password --quiet radicale
  > sudo chown -R radicale /etc/radicale
  > sudo chown /var/lib/radicale

Creation of the virtual environment (manual install only)
---------------------------------------------------------

.. sourcecode:: bash

  > sudo -u radicale virtualenv /var/lib/radicale/env

Installing radicale oauth plugin
--------------------------------

You need to install ``radicale-modoboa-auth-oauth2`` python package inside radicale venv.
If you used the installer you can use the following commands:

.. sourcecode:: bash

  > sudo -u radicale -i bash
  > cd ~
  > env/bin/pip install radicale-modoboa-auth-oauth2

For manual installations, this will do the job:

.. sourcecode:: bash

  > sudo -u radicale /var/lib/radicale/env/bin/pip install radicale-modoboa-auth-oauth2

Please note because the plugin offered by modoboa's team is listing radicale as a dependency you do not need to explicitely install radicale.

Oauth application creation
--------------------------

You first need to register Radicale as an authorized consumer of the
OAuth2 authentication service provided by Modoboa. To do so, create an
application with the following commands:

.. sourcecode:: bash

   > cd <modoboa_instance_path>
   > python manage.py createapplication --name=Radicale --skip-authorization --client-id=radicale confidential client-credentials

On success, you should see an output similar to::

  New application Radicale created successfully.
  client_secret: XXXX

To enable OAuth2 authentication in Radicale, edit the :file:`/etc/radicale/config`
file and update the `type` in `[auth]` to::

  type = radicale_modoboa_auth_oauth2

Then, add the following line in `[auth]`::

  oauth2_introspection_endpoint = https://radicale:<client_secret>@<hostname of your server>/api/o/introspect/


Replace ``<client_secret>`` with the value you obtained earlier.

Your :file:`/etc/radicale/config` should look like this (listening address and port may vary)::

  [server]
  hosts = 0.0.0.0:5232,[::]:5232
  
  [auth]
  type = radicale_modoboa_auth_oauth2
  oauth2_introspection_endpoint = https://radicale:<client_secret>@<hostname of your server>/api/o/introspect/
  
  [rights]
  type = from_file
  file = /etc/radicale/rights
  
  [storage]
  filesystem_folder = /var/lib/radicale/collections

With that set-up, radicale should be working when managing calendars through modoboa's web interface but _not_ when using other clients like Thunderbird.

Modifications for using external clients (optional)
---------------------------------------------------

To ensure other clients can identify, you need to modify radicale by adding in the config file under the [auth] section::

  dovecot_socket = /run/dovecot/auth-radicale

and in 10-master.conf for dovecot::

  unix_listener auth-radicale {
   mode = 0660
   user = radicale
   group = dovecot        
  }

Then, restart both modoboa and radicale to enjoy managing calendars (ICS type) with your favorite client.

Reverse proxy for radicale (optional)
-------------------------------------

At this stage, no encryption is provided, and you may use a reverse proxy as described in `Radicale's documentation
<https://radicale.org/v3.html#reverse-proxy>`_.
