.. _webservers:

###########
Web servers
###########

.. _apache2:

*******
Apache2
*******

.. note:: 

   The following instructions are meant to help you get your site up
   and running quickly. However it is not possible for the people
   contributing documentation to Modoboa to test every single
   combination of web server, wsgi server, distribution, etc. So it is
   possible that **your** installation of uwsgi or nginx or Apache or
   what-have-you works differently. Keep this in mind.

mod_wsgi
========

First, make sure that mod_wsgi is installed on your server.

Create a new virtualhost in your Apache configuration and put the
following content inside::

  <VirtualHost *:80>
    ServerName <your value>
    DocumentRoot <path to your site's dir>

    Alias /media/ <path to your site's dir>/media/
    <Directory <path to your site's dir>/media>
      Order deny,allow
      Allow from all
    </Directory>

    Alias /sitestatic/ <path to your site's dir>/sitestatic/
    <Directory <path to your site's dir>/sitestatic>
      Order deny,allow
      Allow from all
    </Directory>

    WSGIScriptAlias / <path to your site's dir>/wsgi.py
  </VirtualHost>

This is just one possible configuration.

To use mod_wsgi daemon mode, add the two following directives just
under ``WSGIScriptAlias``::

  WSGIDaemonProcess example.com python-path=<path to your site's dir>:<virtualenv path>/lib/python2.7/site-packages
  WSGIProcessGroup example.com

Replace values between ``<>`` with yours. If you don't use a
`virtualenv <http://virtualenv.readthedocs.org/en/latest/>`_, just
remove the last part of the ``WSGIDaemonProcess`` directive.

.. note::
   You will certainly need more configuration in order to launch
   Apache.

.. _nginx-label:

*****
Nginx
*****

.. note:: 

   The following instructions are meant to help you get your site up
   and running quickly. However it is not possible for the people
   contributing documentation to Modoboa to test every single
   combination of web server, wsgi server, distribution, etc. So it is
   possible that **your** installation of uwsgi or nginx or Apache or
   what-have-you works differently. Keep this in mind.

This section covers two different ways of running Modoboa behind
`Nginx <http://nginx.org/>`_ using a WSGI application server. Choose
the one you prefer between `Green Unicorn <http://gunicorn.org/>`_ or
`uWSGI <https://github.com/unbit/uwsgi>`_.

In both cases, you'll need to download and `install nginx
<http://wiki.nginx.org/Install>`_.

Green Unicorn
=============

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
  $ gunicorn -c gunicorn.conf.py <modoboa dir>.wsgi:application

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
        root <modoboa's root dir>;

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
``<>`` with yours), restart nginx and enjoy a really fast
application!

uWSGI
=====

The following setup is meant to get you started quickly. You should
read the documentation of both nginx and uwsgi to understand how to
optimize their configuration for your site.

The Django documentation includes the following warning regarding
uwsgi:

.. warning:: 

   Some distributions, including Debian and Ubuntu, ship an outdated
   version of uWSGI that does not conform to the WSGI
   specification. Versions prior to 1.2.6 do not call close on the
   response object after handling a request. In those cases the
   request_finished signal isn’t sent. This can result in idle
   connections to database and memcache servers.

Use uwsgi 1.2.6 or newer. If you do not, you *will* run into
problems. Modoboa will fail in obscure ways.

To use this setup, first `download and install uwsgi
<http://uwsgi-docs.readthedocs.org/en/latest/WSGIquickstart.html>`_.

Here is a sample nginx configuration::

    server {
        listen 443 ssl;
        ssl on;
        keepalive_timeout 70;

        server_name <host fqdn>;
        root <modoboa's settings dir>;

        ssl_certificate     <ssl certificate for your site>;
        ssl_certificate_key <ssl certificate key for your site>;

        access_log  /var/log/nginx/<host fqdn>.access.log;
        error_log /var/log/nginx/<host fqdn>.error.log;

        location <modoboa's root url>/sitestatic/ {
                autoindex on;
                alias <location of sitestatic on your file system>;
        }

        # Whether or not Modoboa uses a media directory depends on how
        # you configured Modoboa. It does not hurt to have this.
        location <modoboa's root url>/media/ {
                autoindex on;
                alias <location of media on your file system>;
        }

        # This denies access to any file that begins with
        # ".ht". Apache's .htaccess and .htpasswd are such files. A
        # Modoboa installed from scratch would not contain any such
        # files, but you never know what the future holds.
        location ~ /\.ht {
            deny all;
        }

        location <modoba's root url>/ {
            include uwsgi_params;
            uwsgi_pass <uwsgi port>;
            uwsgi_param UWSGI_SCRIPT <modoboa instance name>.wsgi:application;
            uwsgi_param UWSGI_SCHEME https;
        }
    }

``<modoboa instance name>`` must be replaced by the value you used
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

``<modoboa's settings dir>``
  Where Modoboa's :file:`settings.py` resides. This is also where the
  :file:`sitestatic` and :file:`media` directories reside.

``<modoboa's root url>``
  This is the URL which will be the root of your Modoboa site at your
  domain. For instance, if your Modoboa installation is reachable at
  at ``https://foo/modoboa`` then ``<modoboa's root url>`` is
  ``/modoboa``.  In this case you probably also have to set the
  ``alias`` directives to point to where Modoboa's sitestatic and
  media directories are because otherwise nginx won't be able to find
  them.

  If Modoboa is at the root of your domain, then ``<modoboa root
  url>`` is an empty string and can be deleted from the configuration
  above. In this case, you probably do not need the ``alias``
  directives.

``<uwsgi port>``
  The location where uwsig is listening. It could be a unix domain
  socket or an address:port combination. Ubuntu configures uwsgi so
  that the port is::

      unix:/run/uwsgi/app/<app name>/socket

  where ``<app name>`` is the name of the application.

Your uwsgi configuration should be::

    [uwsgi]
    # Not needed when using uwsgi from pip
    # plugins = python
    chdir = <modoboa's top dir>
    module = <name>.wsgi:application
    master = true
    harakiri = 60
    processes = 4
    vhost = true
    no-default-app = true

The plugins directive should be turned on if you use a uwsgi
installation that requires it. If uwsgi was installed from pip, it
does not require it. In the configuration above:

``<modoboa's top dir>``
  The directory where :file:`manage.py` resides. This directory is the
  parent of ``<modoboa's settings dir>``

``<name>``
  The name that you passed to ``modoboa-admin.py deploy`` when you
  created your Modoboa instance.
