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
administrator that can also manipulate domains and assign permissions
to domain administrators.

If you don't want to limit a particular object type, just set the
associated value to -1.

Default limits applied to new administrators can be changed through
the *Modoboa > Parameters > Limits* page.

*****************************
Postfix relay domains support
*****************************

This plugin adds the support for relay domains using postfix. You can
use it when the MTA managed by Modoboa is not the final destination of
one or several domains.

If activated, two new objects will be available from the *Domains*
listing page: *relay domain* and *relay domain alias*.

The extension is compatible with the *amavis* and *limits*
ones. Resellers will be able to create both new objects.

Replace <driver> by the name of the database you use.To tell Postfix this feature exists, you must generate two new map
files and then update your configuration.

To generate the map files, run the following command::

  $ modoboa-admin.py postfix_maps --categories relaydomains --dbtype <the database you use> <path>

Replace values between ``<>`` by yours.

Edit the :file:`/etc/postfix/main.cf` file and copy the following
lines inside::

  relay_domains = <driver>:/etc/postfix/sql-relaydomains.cf
  transport_maps = 
      <driver>:/etc/postfix/sql-relaydomains-transport.cf
      <driver>:/etc/postfix/sql-relaydomain-aliases-transport.cf

  smtpd_recipient_restrictions =
      permit_mynetworks
      reject_unauth_destination
      check_recipient_access 
          <driver>:/etc/postfix/sql-relay-recipient-verification.cf

Replace ``<driver>`` by the name of the database you use.

Reload postfix.

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

.. note::

   The per-domain policies feature only works for new
   installations. Currently, you can't use modoboa with an existing
   database (ie. with data in ``users`` and ``policies`` tables).

.. note::

   This plugin requires amavisd-new version **2.7.0** or higher. If
   you're planning to use the :ref:`selfservice`, you'll need version
   **2.8.0**.

Quick Amavis setup
==================

By default, amavis doesn't use a database. To configure this
behaviour, you first need to create a dedicated database. This step is a
bit manual since no *ready-to-use* SQL schema is provided by
amavis. The information is located inside README files, one for `MySQL
<http://www.amavis.org/README.sql-mysql.txt>`_ and one for `PostgreSQL
<http://www.amavis.org/README.sql-pg.txt>`_.

Then, you must tell amavis to use this database for lookups and
quarantined messages storing. Here is a working configuration sample::

  @lookup_sql_dsn =
    (['DBI:<driver>:database=<database>;host=<dbhost>;port=<dbport>', '<dbuser>', '<password>]']);

  @storage_sql_dsn =
    (['DBI:<driver>:database=<database>;host=<dbhost>;port=<dbport>', '<dbuser>', '<password>]']);

  # PostgreSQL users NEED this parameter!
  # MySQL users only need this parameter is email addresses are stored
  # using the VARBINARY type.
  $sql_allow_8bit_address = 1;

  $virus_quarantine_method = 'sql:';
  $spam_quarantine_method = 'sql:';
  $banned_files_quarantine_method = 'sql:';
  $bad_header_quarantine_method = 'sql:';

  $virus_quarantine_to = 'virus-quarantine';
  $banned_quarantine_to = 'banned-quarantine';
  $bad_header_quarantine_to = 'bad-header-quarantine';
  $spam_quarantine_to = 'spam-quarantine';

Replace values between ``<>`` by yours. To know how to configure
amavis to allow quarantined messages release, read this :ref:`section
<amavis_release>`.

.. note::

   Amavis configuration allows for separate lookup and storage
   databases but Modoboa doesn't support it yet.

Connect Modoboa and Amavis
==========================

You must tell to Modoboa where it can find the amavis
database. Inside :file:`settings.py`, add a new connection to the
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
  #
  # Or like this if you use a virtual environment:
  # 0 0 * * * <virtualenv path/bin/python> <modoboa_site>/manage.py qcleanup

Replace ``modoboa_site`` with the path of your Modoboa instance.

By default, messages older than 14 days are automatically purged. You
can modify this value by changing the ``MAX_MESSAGES_AGE`` parameter
in the online panel.

.. _amavis_release:

Release messages
================

To release messages, first take a look at `this page
<http://www.ijs.si/software/amavisd/amavisd-new-docs.html#quar-release>`_. It
explains how to configure amavisd-new to listen somewhere for the
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

Once amavisd-new is configured, just tell Modoboa where it can find
the *release server* by modifying the following parameters in the
online panel:

+--------------------+--------------------+------------------------+
|Name                |Description         |Default value           |
+====================+====================+========================+
|Amavis connection   |Mode used to access |unix                    |
|mode                |the PDP server      |                        |
+--------------------+--------------------+------------------------+
|PDP server address  |PDP server address  |localhost               |
|                    |(if inet mode)      |                        |
+--------------------+--------------------+------------------------+
|PDP server port     |PDP server port (if |                        |
|                    |inet mode) 9998     |                        |
+--------------------+--------------------+------------------------+
|PDP server socket   |Path to the PDP     |/var/amavis/amavisd.sock|
|                    |server socket (if   |                        |
|                    |unix mode)          |                        |
+--------------------+--------------------+------------------------+

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
  #
  # Or like this if you use a virtual environment:
  # 0 12 * * * <virtualenv path/bin/python> <modoboa_site>/manage.py amnotify --baseurl='<modoboa_url>'

You are free to change the frequency.

.. note::

  If you want to let users release their messages alone (not
  recommended), go to the admin panel.

The following parameters are available to let you customize this
feature:

+--------------------+--------------------+------------------------+
|Name                |Description         |Default value           |
+====================+====================+========================+
|Check requests      |Interval between two|30                      |
|interval            |release requests    |                        |
|                    |checks              |                        |
+--------------------+--------------------+------------------------+
|Allow direct release|Allow users to      |no                      |
|                    |directly release    |                        |
|                    |their messages      |                        |
+--------------------+--------------------+------------------------+
|Notifications sender|The e-mail address  |notification@modoboa.org|
|                    |used to send        |                        |
|                    |notitications       |                        |
+--------------------+--------------------+------------------------+

.. _selfservice:

Self-service mode
=================

The *self-service* mode lets users act on quarantined messages without
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
**Enable self-service mode** parameter to yes.

The last step is to customize the notification messages amavis
sends. The most important is to embark a direct link. Take a look at
the `README.customize <http://amavis.org/README.customize.txt>`_ file to
learn what you're allowed to do.

Here is a link example::

  http://<modoboa_url>/quarantine/%i/?rcpt=%R&secret_id=[:secret_id]

Manual SpamAssassin learning
============================

It is possible to manually train SpamAssassin (FIXME: URL) using
the quarantine's content. By train, we mean:

* Mark message(s) as spam (false negative(s))

* Mark message(s) as non-spam (false positive(s))

This feature is available to all users (from super administrators to
simple users) but not enabled by default.

SpamAssassin configuration
--------------------------

For better performance and to enable the per-user level, SpamAssassin
must store bayes information into a SQL database.

Create a new database and a new user/password (using your favorite
database server) and edit the default configuration file
(:file:`/etc/spamassassin/local.cf`) to add the following lines
inside:

.. sourcecode:: perl

  bayes_store_module    Mail::SpamAssassin::BayesStore::<Driver>
  bayes_sql_dsn         <DSN>
  bayes_sql_username    <db username>
  bayes_sql_password    <db password>

Replace values between ``<>`` by yours. Possible values for ``Driver``
are ``PgSQL`` or ``MySQL`` (non exhaustive list). The syntax for
``DSN`` depends on the driver you choose. Please consult the official
documentation. (FIXME: URL)

Enable the feature through Modoboa
----------------------------------

Manual learning is disabled by default. You can activate it through
the administration panel (*Modoboa > Paremeters > Amavis*). There two
learning levels:

#. Global: available to administrators only. A single (global) bayes
   database is shared between everyone.

#. Per domain: available to administrators and domain
   administrators. Each domain can have a dedicated database.

#. Per user: each user can create its own database to customize the
   way SpamAssassin will detect spam.

The domain and user levels are not activated by default, dedicated
parameters are available through the panel.

.. note::

   Domain and user databases are only created the first time someone
   calls the learning feature through the quarantine.

.. warning::

   A bayes database needs to reach pre-defined thresholds before it
   can be used by SpamAssassin. The default values are **200** spams
   and **200** hams.

You will find other paramaters related to this feature. You won't need
to change them most of the time, unless SpamAssassin is hosted on a
different machine than Modoboa. (in this case, ``spamc`` will be used
instead of ``sa-learn``).

.. _stats:

********************
Graphical statistics
********************

This plugin collects various statistics about emails traffic on your
server. It parses a log file to collect information, store it into RRD
files (see `rrdtool <http://oss.oetiker.ch/rrdtool/>`_) and then
generates graphics in PNG format.

To use it, go to the online parameters panel and adapt the following
ones to your environment:

+--------------------+--------------------+--------------------------+
|Name                |Description         |Default value             |
+====================+====================+==========================+
|Path to the log file|Path to log file    |/var/log/mail.log         |
|                    |used to collect     |                          |
|                    |statistics          |                          |
+--------------------+--------------------+--------------------------+
|Directory to store  |Path to directory   |/tmp/modoboa              |
|RRD files           |where RRD files are |                          |
|                    |stored              |                          |
+--------------------+--------------------+--------------------------+
|Directory to store  |Path to directory   |<modoboa_site>/media/stats|
|PNG files           |where PNG files are |                          |
|                    |stored              |                          |
+--------------------+--------------------+--------------------------+

Make sure the directory that will contain RRD files exists. If not,
create it before going further. For example (according to the previous
parameters)::

  $ mkdir /tmp/modoboa

To finish, you need to collect information periodically in order to
feed the RRD files. Add the following line into root's crontab::

  */5 * * * * <modoboa_site>/manage.py logparser &> /dev/null
  #
  # Or like this if you use a virtual environment:
  # 0/5 * * * * <virtualenv path/bin/python> <modoboa_site>/manage.py logparser &> /dev/null

Replace ``<modoboa_site>`` with the path of your Modoboa instance.

Graphics will be automatically created after each parsing.

.. _postfix_ar:

***************************
Postifx auto-reply messages
***************************

This plugin let users define an auto-reply message (*vacation*). It is
based on Postfix capabilities.

The user that executes the autoreply script needs to access
:file:`settings.py`. You must apply proper permissions on this file. For
example, if :file:`settings.py` belongs to ``www-data:www-data``, you can add
the ``vmail`` user to the ``www-data`` group and set the read permission
for the group.

To make Postfix use this feature, you need to update your
configuration files as follows:

``/etc/postfix/main.cf``::

  transport_maps = <driver>:/etc/postfix/sql-autoreplies-transport.cf
  virtual_alias_maps = <driver>:/etc/postfix/sql-aliases.cf
          <driver>:/etc/postfix/sql-domain-aliases-mailboxes.cf,
          <driver>:/etc/postfix/sql-autoreplies.cf,
          <driver>:/etc/postfix/sql-catchall-aliases.cf

.. note::

   The order used to define alias maps is important, please respect it

``/etc/postfix/master.cf``::

  autoreply unix        -       n       n       -       -       pipe
            flags= user=vmail:<group> argv=python <modoboa_site>/manage.py autoreply $sender $mailbox

Replace ``<driver>`` by the name of the database you
use. ``<modoboa_site>`` is the path of your Modoboa instance.

Then, create the requested map files::

  $ modoboa-admin.py postfix_maps mapfiles --categories autoreply

`mapfiles` is the directory where the files will be stored. Answer the
few questions and you're done.

.. note::

   Auto-reply messages are just sent one time per sender for a
   pre-defined time period. By default, this period is equal to 1 day
   (86400s), you can adjust this value by modifying the **Automatic
   reply timeout** parameter available in the online panel.

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
language. Don't panic, Dovecot supports both :-) (refer to
:ref:`dovecot` to know how to enable those features).

.. note:: 
   The sieve filters plugin requires that the :ref:`webmail` plugin is
   activated and configured.

Go the online panel and modify the following parameters in order to
communicate with the *ManageSieve* server:

+--------------------+--------------------+--------------------+
|Name                |Description         |Default value       |
+====================+====================+====================+
|Server address      |Address of your     |127.0.0.1           |
|                    |MANAGESIEVE server  |                    |
+--------------------+--------------------+--------------------+
|Server port         |Listening port of   |4190                |
|                    |your MANAGESIEVE    |                    |
|                    |server              |                    |
+--------------------+--------------------+--------------------+
|Connect using       |Use the STARTTLS    |no                  |
|STARTTLS            |extension           |                    |
+--------------------+--------------------+--------------------+
|Authentication      |Prefered            |auto                |
|mechanism           |authentication      |                    |
|                    |mechanism           |                    |
+--------------------+--------------------+--------------------+

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
to communicate with your *IMAP* server (under *IMAP settings*):

+--------------------+--------------------+--------------------+
|Name                |Description         |Default value       |
+====================+====================+====================+
|Server address      |Address of your IMAP|127.0.0.1           |
|                    |server              |                    |
+--------------------+--------------------+--------------------+
|Use a secured       |Use a secured       |no                  |
|connection          |connection to access|                    |
|                    |IMAP server         |                    |
+--------------------+--------------------+--------------------+
|Server port         |Listening port of   |143                 |
|                    |your IMAP server    |                    |
+--------------------+--------------------+--------------------+

Do the same to communicate with your SMTP server (under *SMTP settings*):

+--------------------+--------------------+--------------------+
|Name                |Description         |Default value       |
+====================+====================+====================+
|Server address      |Address of your SMTP|127.0.0.1           |
|                    |server              |                    |
+--------------------+--------------------+--------------------+
|Secured connection  |Use a secured       |None                |
|mode                |connection to access|                    |
|                    |SMTP server         |                    |
+--------------------+--------------------+--------------------+
|Server port         |Listening port of   |25                  |
|                    |your SMTP server    |                    |
+--------------------+--------------------+--------------------+
|Authentication      |Server needs        |no                  |
|required            |authentication      |                    |
+--------------------+--------------------+--------------------+

.. note::

   The size of each attachment sent with messages is limited. You can
   change the default value by modifying the **Maximum attachment
   size** parameter.

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
