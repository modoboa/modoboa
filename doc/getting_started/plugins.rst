#############
Using plugins
#############

**************************
Enable or disable a plugin
**************************

Starting with 0.8.2, Modoboa provides an online panel to control
plugins activation:

* To activate a plugin, go to the *admin -> settings -> extensions* page,
  check the corresponding box and click on the *Apply* button.
* To deactivate a plugin, go to the *admin -> settings -> extensions* page,
  uncheck the corresponding box and click on the *Apply* button.

****************
Per-admin limits
****************

This extension offers a way to define limits about how many objects
(aliases, mailboxes) a domain administrator can create.

It also brings a new role: ``Reseller``. A reseller is a domain
administrator that can also manipulates domains and assign permissions
to domain administrators.

If you don't want to limit particular object type, just set the
associated value to -1.

********************
Amavisd-new frontend
********************

This plugin provides a simple management frontend for
*amavisd-new*. The supported features are:

* SQL quarantine management : available to administrators or users,
  possibility to delete or release messages
* Per domain customization (using policies): specify how amavisd-new
  will handle traffic

To use it, you first need to specify where the database that contains the
quarantine is. Inside *settings.py*, add a new connection to the
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

To be able to release messages, first take a look at `this page
<http://www.ijs.si/software/amavisd/amavisd-new-docs.html#quar-release>`_. It
explains how to configure *amavisd-new* to listen somewhere for the
AM.PDP protocol. This protocol is used to send release requests.

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
admin panel::

  # "unix" or "inet"
  AM_PDP_MODE = "inet"

  # "unix" mode only
  AM_PDP_SOCKET = "/var/amavis/amavisd.sock"

  # "inet" mode only
  AM_PDP_HOST = "127.0.0.1"
  AM_PDP_PORT = 9998

By default, simple users are not allowed to release messages
themselves. They are only allowed to send release requests to
administrators. 

As administrators are not always available or logged into Modoboa, a
notification tool is available. It sends reminder e-mails to every
administrators or domain administrators. To use it, add the following
example line to root's crontab::

  0 12 * * * <modoboa_site>/manage.py amnotify --baseurl='<modoboa_url>'

You are free to change the frequency.

If you want to let users release their messages alone (not
recommanded), change the value of the ``USER_CAN_RELEASE`` parameter
into the admin panel.

Last step: Modoboa provides a simple script that periodically purges
the quarantine database. To use it, add the following line inside
root's crontab::

  0 0 * * * <modoboa_site>/manage.py qcleanup

Replace ``modoboa_site`` with the path of your Modoboa instance.

By default, messages older than 14 days are automatically purged. You
can modify this value by changing the ``MAX_MESSAGES_AGE`` parameter
in the admin panel.

********************
Graphical statistics
********************

This plugin collects various statistics about emails traffic on your
server. It parses log file to collect information and then generates
graphics using the PNG format.

First, adapt the following parameters to your environnement::

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
feed the RRD files. To do so, add the following line into root's
crontab::

  */5 * * * * <modoboa_site>/manage.py logparser &> /dev/null

Replace ``modoboa_site`` with the path of your Modoboa instance.

Graphics will be automatically created after each parsing.

***************************
Postifx auto-reply messages
***************************

Allow users to define an auto-reply message. This plugin is based on
*postfix* capabilities.

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

For *MySQL* users, create new map files with the following content:

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
   parameter available in the admin panel.

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

To use this plugin, your hosting setup must include a ManageSieve
server and your IMAP server must support the Sieve language. Don't
panic, Dovecot supports both :-)

Refer to :ref:`dovecot` section if you want to active those
features into Dovecot.

.. note:: 
   The sieve filters plugin requires that the webmail plugin is
   activated and configured.

Go the admin panel and modify plugin's parameters in order to
communicate with the ManageSieve server (default values are displayed
below)::

  SERVER = localhost
  PORT = 2000
  STARTTLS = no
  AUTHENTICATION_MECH = plain

*******
Webmail
*******

Modoboa provides a simple webmail (you can browse, read and compose
messages). With this feature, it is possible to deploy an almost
standalone mail hosting platform just with Modoboa.

To use it, go to the admin panel and modify the following parameters
in order to communicate with your IMAP and SMTP servers (default
values are displayed below)::

  IMAP_SECURED = no
  IMAP_SERVER = 127.0.0.1
  IMAP_PORT = 143

  SMTP_SECURED_MODE = None
  SMTP_AUTHENTICATION = no
  SMTP_SERVER = 127.0.0.1
  SMTP_PORT = 25

The webmail supports the sending of attachments with messages. You can
limit the size of each attachment by going to the *Admin > Settings >
Parameters* page. Click on the ``webmail`` tab and modify the value of
the ``MAX_ATTACHMENT_SIZE`` parameter.
