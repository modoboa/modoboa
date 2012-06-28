#############
Using plugins
#############

**************************
Enable or disable a plugin
**************************

Modoboa provides an online panel to control plugins activation. You
will find it at *Modoboa > Extensions*. 

To activate a plugin, check the corresponding box and click on the
*Apply* button.

To deactivate a plugin, uncheck the corresponding box and click on the
*Apply* button.

****************
Per-admin limits
****************

This plugin offers a way to define limits about how many objects
(aliases, mailboxes) a domain administrator can create.

It also brings a new administrative role: ``Reseller``. A reseller is a domain
administrator that can also manipulates domains and assign permissions
to domain administrators.

If you don't want to limit a particular object type, just set the
associated value to -1.

.. _amavis_frontend:

********************
Amavisd-new frontend
********************

This plugin provides a simple management frontend for `amavisd-new
<http://www.amavis.org>`_. The supported features are:

* SQL quarantine management : available to administrators or users,
  possibility to delete or release messages
* Per domain customization (using policies): specify how amavisd-new
  will handle traffic

Database
========

You must specify to Modoboa where it can find the amavis
database. Inside *settings.py*, add a new connection to the
``DATABASES`` variable like this::

  DATABASES = {
    # Stuff before
    #
    "amavis": {
      "ENGINE" : "<your value>",
      "HOST" : "<your value>",
      "NAME" : "<your value>",
      "USER" : "<your value>",
      "PASSWORD" : "<your value>"
    }
  }    

Replace values between ``<>`` with yours.

Cleanup
-------

Storing quarantined messages to a database can quickly become a
perfomance killer. Modoboa provides a simple script to periodically
purge the quarantine database. To use it, add the following line
inside root's crontab::

  0 0 * * * <modoboa_site>/manage.py qcleanup

Replace ``modoboa_site`` with the path of your Modoboa instance.

By default, messages older than 14 days are automatically purged. You
can modify this value by changing the ``MAX_MESSAGES_AGE`` parameter
in the online panel.

Release messages
================

To release messages, first take a look at `this page
<http://www.ijs.si/software/amavisd/amavisd-new-docs.html#quar-release>`_. It
explains how to configure *amavisd-new* to listen somewhere for the
AM.PDP protocol. This protocol is used to send requests.

Below is an example of a working configuration::

  $interface_policy{'SOCK'} = 'AM.PDP-SOCK';
  $interface_policy{'9998'} = 'AM.PDP-INET';

  $policy_bank{'AM.PDP-SOCK'} = {
    protocol => 'AM.PDP',
    auth_required_release => 0,
  };
  $policy_bank{'AM.PDP-INET'} = {
    protocol => 'AM.PDP',
    inet_acl => [qw( 127.0.0.1 [::1] )],
  };

Don't forget to update the ``inet_acl`` list if you plan to release from
the network.

Once *amavisd-new* is configured, just tell Modoboa where it can find
the *release server* by modifying the following parameters in the
online panel::

  # "unix" or "inet"
  AM_PDP_MODE = "inet"

  # "unix" mode only
  AM_PDP_SOCKET = "/var/amavis/amavisd.sock"

  # "inet" mode only
  AM_PDP_HOST = "127.0.0.1"
  AM_PDP_PORT = 9998

Deferred release
----------------

By default, simple users are not allowed to release messages
themselves. They are only allowed to send release requests to
administrators. 

As administrators are not always available or logged into Modoboa, a
notification tool is available. It sends reminder e-mails to every
administrators or domain administrators. To use it, add the following
example line to root's crontab::

  0 12 * * * <modoboa_site>/manage.py amnotify --baseurl='<modoboa_url>'

You are free to change the frequency.

.. note::

  If you want to let users release their messages alone (not
  recommanded), change the value of the ``USER_CAN_RELEASE`` parameter
  into the admin panel.

Self-service mode
=================

The *self-service* mode let users act on quarantined messages without
beeing authenticated. They can:

* View messages
* Remove messages
* Release messages (or send release requests)

To access a specific message, they only need the following information:

* Message's unique identifier
* Message's secret identifier

This information is controlled by *amavis*, which is in charge of
notifying users when new messages are put into quarantine. Each
notification (one per message) must embark a direct link containing
the required identifiers.

To activate this feature, go the administration panel and set the
``SELF_SERVICE`` paramater to yes.

The last step is to customize the notification messages *amavis*
sends. The most important is to embark a direct link. Take a look at
the `README.customize <http://amavis.org/README.customize.txt>`_ file to
learn what you're allowed to do.

Here is a link example::

  http://<modoboa_url>/quarantine/%i/?rcpt=%R&secret_id=[:secret_id]

.. _stats:

********************
Graphical statistics
********************

This plugin collects various statistics about emails traffic on your
server. It parses a log file to collect information, store it into RRD
files (see `rrdtool <http://oss.oetiker.ch/rrdtool/>`_)and then
generates graphics in PNG format.

To use it, go to the online parameters panel and adapt the following
ones to your environnement::

  # Path to mail log file
  LOGFILE = "/var/log/mail.log"

  # Path to directory where rrd files are stored
  RRD_ROOTDIR = "/tmp/modoboa"

  # Path to directory where png files are stored
  IMG_ROOTDIR = "<modoboa_site>/media/stats"

Make sure the directory that will contain RRD files exists
(``RRD_ROOTDIR``). If not, create it before going further. For example
(according to the previous parameters)::

  $ mkdir /tmp/modoboa

To finish, you need to collect information periodically in order to
feed the RRD files. Add the following line into root's crontab::

  */5 * * * * <modoboa_site>/manage.py logparser &> /dev/null

Replace ``<modoboa_site>`` with the path of your Modoboa instance.

Graphics will be automatically created after each parsing.

.. _postfix_ar:

***************************
Postifx auto-reply messages
***************************

This plugin let users define an auto-reply message (*vacation*). It is
based on *postfix* capabilities.

The user that executes the autoreply script needs to access
*settings.py*. You must apply proper permissions on this file. For
example, if *settings.py* belongs to *www-data:www-data*, you can add
the *vmail* user to the *www-data* group and set the read permission
for the group.

To make *postfix* use this feature, you need to update your
configuration files as follow:

``/etc/postfix/main.cf``::

  transport_maps = mysql:/etc/postfix/maps/sql-transport.cf
  virtual_alias_maps = mysql:/etc/postfix/maps/sql-aliases.cf
          mysql:/etc/postfix/maps/sql-autoreplies.cf

``/etc/postfix/master.cf``::

  autoreply unix        -       n       n       -       -       pipe
            flags= user=vmail:<group> argv=<modoboa_site>/manage.py autoreply $sender $mailbox

``<modoboa_site>`` is the path of your Modoboa instance.

Then, create new map files with the following content:

``/etc/postfix/maps/sql-transport.cf``::

  user = <user>
  password = <password>
  dbname = <database>
  hosts = 127.0.0.1
  query = SELECT method FROM postfix_autoreply_transport WHERE domain='%s'

``/etc/postfix/maps/sql-autoreplies.cf``::

  user = <user>
  password = <password>
  dbname = <database>
  hosts = 127.0.0.1
  query = SELECT full_address, autoreply_address FROM postfix_autoreply_alias WHERE full_address='%s'

.. note::
   Auto-reply messages are just sent one time per sender for a
   pre-defined time period. By default, this period is equal to 1 day
   (86400s), you can adjust this value by modifying the ``AUTOREPLY_TIMEOUT``
   parameter available in the online panel.

*************
Sieve filters
*************

This plugin let users create server-side message filters, using the
`sievelib module <http://pypi.python.org/pypi/sievelib>`_ (which
provides Sieve and ManageSieve clients).

Two working modes are available:

* A raw mode: you create filters using the Sieve language directly
  (advanced users)
* An assisted mode: you create filters using an intuitive form

To use this plugin, your hosting setup must include a *ManageSieve*
server and your local delivery agent must understand the *Sieve*
language. Don't panic, *Dovecot* supports both :-) (refer to
:ref:`dovecot` to know how to enable those features).

.. note:: 
   The sieve filters plugin requires that the :ref:`webmail` plugin is
   activated and configured.

Go the online panel and modify the following parameters in order to
communicate with the *ManageSieve* server (default values are displayed
below)::

  SERVER = localhost
  PORT = 2000
  STARTTLS = no
  AUTHENTICATION_MECH = plain

.. _webmail:

*******
Webmail
*******

Modoboa provides a simple webmail:

* Browse, read and compose messages, attachments are supported
* HTML messages are supported
* `CKeditor <http://ckeditor.com/>`_ integration
* Manipulate mailboxes (create, move, remove)
* Quota display

To use it, go to the online panel and modify the following parameters
in order to communicate with your *IMAP* and *SMTP* servers (default
values are displayed below)::

  IMAP_SECURED = no
  IMAP_SERVER = 127.0.0.1
  IMAP_PORT = 143

  SMTP_SECURED_MODE = None
  SMTP_AUTHENTICATION = no
  SMTP_SERVER = 127.0.0.1
  SMTP_PORT = 25

The size of each attachment sent with messages is limited. You can
change the default value by modifying the ``MAX_ATTACHMENT_SIZE``
parameter.

Using CKeditor
==============

Modoboa supports CKeditor to compose HTML messages. To use it, first
download it from `the official website <http://ckeditor.com/>`_, then
extract the tarball::

  $ cd <modoboa_site_dir>
  $ tar xzf /path/to/ckeditor/tarball.tag.gz -C sitestatic/js/

And you're done!

Now, each user has the possibility to choose between CKeditor and the
raw text editor to compose their messages. (see *User > Settings >
Preferences > Webmail*)
