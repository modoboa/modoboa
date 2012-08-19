.. _webservers:

###########
Web servers
###########

.. _apache2:

*******
Apache2
*******

First, make sure that both *apache2* and *mod_python* are installed on
your server.

Create a new virtualhost in your Apache configuration and put the
following inside::

  <VirtualHost *:80>
    <Location "/">
      SetHandler mod_python
      PythonHandler django.core.handlers.modpython
      PythonPath "['<path to directory that contains modoboa dir>'] + sys.path"
      SetEnv DJANGO_SETTINGS_MODULE modoboa.settings
    </Location>
    Alias "/sitestatic" "<path to modoboa dir>/sitestatic"
    <Location "/sitestatic/">
      SetHandler None
    </Location>
    Alias "/media" "<path to modoboa dir>/media"
    <Location "/media/">
      SetHandler None
    </Location>
  </VirtualHost>

This is one possible configuration. Note that you will certainly need more
configuration in order to launch Apache.

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
  $ gunicorn_django -c gunicorn.conf.py

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
