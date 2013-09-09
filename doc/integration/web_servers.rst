.. _webservers:

###########
Web servers
###########

.. _apache2:

*******
Apache2
*******

mod_wgsi
========

First, make sure that *mod_wsgi* is installed on your server.

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

.. note::
   *Django* 1.3 users, please consult this `page <https://docs.djangoproject.com/en/1.3/howto/deployment/modwsgi/>`_,
   it contains an example *wsgi.py* file.

.. note:: 
   You will certainly need more configuration in order to launch
   Apache.

mod_python
==========

First, make sure that *mod_python* is installed on your server.

Create a new virtualhost in your Apache configuration and put the
following content inside::

  <VirtualHost *:80>
    ServerName <your value>
    DocumentRoot <path to your site's dir>

    <Location "/">
      SetHandler mod_python
      PythonHandler django.core.handlers.modpython
      PythonPath "['<path to directory that contains your site's dir>'] + sys.path"
      SetEnv DJANGO_SETTINGS_MODULE <your site's name>.settings
    </Location>

    Alias "/sitestatic" "<path to your site's dir>/sitestatic"
    <Location "/sitestatic/">
      SetHandler None
    </Location>

    Alias "/media" "<path to your site's dir>/media"
    <Location "/media/">
      SetHandler None
    </Location>
  </VirtualHost>

This is just one possible configuration. 

.. note:: 
   You will certainly need more configuration in order to launch
   Apache.

.. _nginx-label:

*****
Nginx
*****

`Nginx <http://nginx.org/>`_ is a really fast HTTP server. Associated
with `Green Unicorn <http://gunicorn.org/>`_, it gives you one of the
best setup to serve python/Django applications. Modoboa's
performances are really good with this configuration.

To use this setup, first download and install those softwares
(`Install gunicorn <http://gunicorn.org/install.html>`_ and `install
nginx <http://wiki.nginx.org/Install>`_).

Then, use the following sample *gunicorn* configuration (create a new
file named *gunicorn.conf.py* inside Modoboa's root dir)::

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

Now the *nginx* part. Just create a new virtual host and use the
following configuration::

  upstream modoboa {
	server      unix:/var/run/gunicorn/modoboa.sock fail_timeout=0;
  }

  server {
        listen 443;
        server_name <host fqdn>;
        root <modoboa's root dir>;

        access_log  /var/log/nginx/<host fqdn>.access.log;
        error_log /var/log/nginx/<host fqdn>.error.log;

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

Paste this content to your configuration (replace values between
``<>`` with yours), restart *nginx* and enjoy a really fast
application!
