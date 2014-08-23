.. _webmail:

#######
Webmail
#######

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
