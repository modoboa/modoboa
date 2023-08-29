.. _webserver:

##########
Web server
##########

.. note::

   The following instructions are meant to help you get your site up
   and running quickly. However it is not possible for the people
   contributing documentation to Modoboa to test every single
   combination of web server, wsgi server, distribution, etc. So it is
   possible that **your** installation of uwsgi or nginx or Apache or
   what-have-you works differently. Keep this in mind.

.. _apache2:

Apache2
*******

First, make sure that ``mod_wsgi`` is installed on your server.

Create a new virtualhost in your Apache configuration and put the
following content inside::

  WSGIPythonHome /var/www/modoboa/env
  WSGIPythonPath /var/www/modoboa/instance

  <VirtualHost *:80>
    ServerName <your value>

    DocumentRoot  <modoboa_instance_path>

    Alias /media/ <modoboa_instance_path>/media/
    <Directory <modoboa_instance_path>/media/>
      Options FollowSymLinks
      Require all granted
    </Directory>

    Alias /sitestatic/ <modoboa_instance_path>/sitestatic/
    <Directory <modoboa_instance_path>/sitestatic/>
      Options FollowSymLinks
      Require all granted
    </Directory>

    Alias /new-admin <modoboa_instance_path>/frontend
    <Directory <modoboa_instance_path>/frontend>
      Options FollowSymLinks
      Require all granted
    </Directory>

    WSGIScriptAlias / <modoboa_instance_path>/instance/wsgi.py
    WSGIApplicationGroup %{GLOBAL}

    # Pass Authorization header to enable API usage:
    WSGIPassAuthorization On

    LogLevel info
  </VirtualHost>

This is just one possible configuration.

Replace values between ``<>`` with yours. If you don't use a
`virtualenv <http://virtualenv.readthedocs.org/en/latest/>`_, just
remove the last part of the ``WSGIDaemonProcess`` directive.
.. note::

  You may need to add::
    import sys

    sys.path.append('<modoboa_instance_path>')
    sys.path.append('<modoboa_venv_path>/bin')
    sys.path.append('<modoboa_venv_path>/lib/python3.X/site-packages')

  in :file:`<modoboa_instance_path>/instance/wsgi.py`.

.. note::

   You will certainly need more configuration in order to launch
   Apache.

Now, you can go the :ref:`dovecot` section to continue the installation.

.. _nginx-label:

Nginx
*****

This section covers two different ways of running Modoboa behind
`Nginx <http://nginx.org/>`_ using a WSGI application server. Choose
the one you prefer between `Green Unicorn <http://gunicorn.org/>`_ or
`uWSGI <https://github.com/unbit/uwsgi>`_.

In both cases, you'll need to download and `install nginx
<http://wiki.nginx.org/Install>`_.

uWSGI
+++++

The following setup is meant to get you started quickly. You should
read the documentation of both nginx and uwsgi to understand how to
optimize their configuration for your site.

The Django documentation includes the following warning regarding
uwsgi:

.. warning::

   Use uwsgi 1.2.6 or newer. If you do not, you *will* run into
   problems. Modoboa will fail in obscure ways.

To use this setup, first `download and install uwsgi
<http://uwsgi-docs.readthedocs.org/en/latest/WSGIquickstart.html>`_.

Recommend packages for debian and derivatives::

  apt install uwsgi uwsgi-plugin-python3

Here is a sample nginx configuration::

  upstream modoboa {
    server unix:<uwsgi_socket_path> fail_timeout=0;
  }

  server {
      listen 80;
      listen [::]:80;
      server_name <hostname>;
      rewrite ^ https://$server_name$request_uri? permanent;
  }

  server {
      listen 443 ssl http2;
      listen [::]:443 ssl http2;
      server_name <hostname>;
      root <modoboa_instance_path>;

      ssl_certificate  <ssl certificate for your site>;
      ssl_certificate_key  <ssl certificate key for your site>;
      ssl_protocols TLSv1.2 TLSv1.3;
      ssl_ciphers "ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-SHA384";
      ssl_prefer_server_ciphers on;
      ssl_session_cache shared:SSL:10m;
      ssl_verify_depth 3;
      ssl_dhparam /etc/nginx/dhparam.pem;

      client_max_body_size 10M;

      access_log /var/log/nginx/modoboa-access.log;
      error_log /var/log/nginx/modoboa-error.log;

      location /sitestatic/ {
          try_files $uri $uri/ =404;
      }

      location /media/ {
          try_files $uri $uri/ =404;
      }

      location ^~ /new-admin {
          alias  <modoboa_instance_path>/frontend/;
          index  index.html;

          expires -1;
          add_header Pragma "no-cache";
          add_header Cache-Control "no-store, no-cache, must-revalidate, post-check=0, pre-check=0";

          try_files $uri $uri/ /index.html = 404;
      }

      location / {
          include uwsgi_params;
          uwsgi_param UWSGI_SCRIPT instance.wsgi:application;
          uwsgi_pass modoboa;
      }
      %{extra_config}
  }

``<modoboa instance name>``, ``<hostname>``, ``<modoboa_instance_path>`` and ``<ssl...>`` must be replaced by the value you used.
``<uwsgi_socket_path>``


when :ref:`you deployed your instance <deployment>`.

If you do not plan to use SSL then change the listen directive to
``listen 80;`` and delete each of the following directives::

    ssl on;
    keepalive_timeout 70;
    ssl_certificate     <ssl certificate for your site>;
    ssl_certificate_key <ssl certificate key for your site>;
    uwsgi_param UWSGI_SCHEME https;

If you do plan to use SSL, you'll have to generate a certificate and a
key. `This article
<http://wiki.nginx.org/HttpSslModule#Generate_Certificates>`_
contains information about how to do it.

Make sure to replace the ``<...>`` in the sample configuration with
appropriate values. Here are some explanations for the cases that may
not be completely self-explanatory:

``<hostname>``
  This is the URL which will be the root of your Modoboa site at your
  domain. For instance, if your Modoboa installation is reachable at
  at ``https://foo/modoboa`` then ``<hostname>`` is
  ``/modoboa``.  In this case you probably also have to set the
  ``alias`` directives to point to where Modoboa's sitestatic and
  media directories are because otherwise nginx won't be able to find
  them.

  If Modoboa is at the root of your domain, then ``<hostname>``
  is an empty string and can be deleted from the configuration
  above. In this case, you probably do not need the ``alias``
  directives.

``<uwsgi_socket_path>``
  The location where uwsig is listening. It could be a unix domain
  socket or an address:port combination. Ubuntu configures uwsgi so
  that the port is::

      unix:/run/uwsgi/app/<app name>/socket

  where ``<app name>`` is the name of the application.

Your uwsgi configuration should be::

    [uwsgi]
    # Not needed when using uwsgi from pip
    # plugins = python
    chdir = <modoboa_instance_path>
    module = <name>.wsgi:application
    master = true
    harakiri = 60
    processes = 4
    vhost = true
    no-default-app = true

The plugins directive should be turned on if you use a uwsgi
installation that requires it. If uwsgi was installed from pip, it
does not require it. In the configuration above:

``<modoboa_instance_path>``
  The directory where :file:`manage.py` resides. This directory is the
  parent of ``<modoboa's settings dir>``

``<name>``
  The name that you passed to ``modoboa-admin.py deploy`` when you
  created your Modoboa instance, usually ``instance``.

Now, you can go the :ref:`dovecot` section to continue the installation.

Green Unicorn
+++++++++++++

Firstly, `Download and install gunicorn
<http://gunicorn.org/install.html>`_. Then, use the following sample
gunicorn configuration (create a new file named
:file:`gunicorn.conf.py` inside Modoboa's root dir)::

  backlog = 2048
  bind = "unix:/var/run/gunicorn/modoboa.sock"
  pidfile = "/var/run/gunicorn/modoboa.pid"
  daemon = True
  debug = False
  workers = 2
  logfile = "/var/log/gunicorn/modoboa.log"
  loglevel = "info"

To start gunicorn, execute the following commands::

  $ cd <modoboa dir>
  $ gunicorn -c gunicorn.conf.py <APP/INSTANCE Name>.wsgi:application

Now the nginx part. Just create a new virtual host and use the
following configuration::

  upstream modoboa {
	server      unix:/var/run/gunicorn/modoboa.sock fail_timeout=0;
  }

  server {
        listen 443 ssl;
        ssl on;
        keepalive_timeout 70;

        server_name <host fqdn>;
        root <modoboa_instance_path>;

        access_log  /var/log/nginx/<host fqdn>.access.log;
        error_log /var/log/nginx/<host fqdn>.error.log;

        ssl_certificate     <ssl certificate for your site>;
        ssl_certificate_key <ssl certificate key for your site>;

        location /sitestatic/ {
                autoindex on;
        }

        location /media/ {
                autoindex on;
        }

        location / {
                proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
                proxy_set_header Host $http_host;
                proxy_redirect off;
                proxy_set_header X-Forwarded-Protocol ssl;
                proxy_pass http://modoboa;
        }
  }

If you do not plan to use SSL then change the listen directive to
``listen 80;`` and delete each of the following directives::

    ssl on;
    keepalive_timeout 70;
    ssl_certificate     <ssl certificate for your site>;
    ssl_certificate_key <ssl certificate key for your site>;
    proxy_set_header X-Forwarded-Protocol ssl;

If you do plan to use SSL, you'll have to generate a certificate and a
key. `This article
<http://wiki.nginx.org/HttpSslModule#Generate_Certificates>`__
contains information about how to do it.

Paste this content to your configuration (replace values between
``<>`` with yours) and restart nginx.

Now, you can go the :ref:`dovecot` section to continue the installation.
