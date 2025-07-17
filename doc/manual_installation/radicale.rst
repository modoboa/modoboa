.. _radicale:

#######
Radicale
#######

This page is currently being written.

.. _dovecot_oauth2:

OAuth 2 authentication
======================

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

  oauth2_introspection_endpoint = https://radical:<client_secret>@<hostname of your server>/api/o/introspect/


Replace ``<client_secret>`` with the value you obtained earlier.
