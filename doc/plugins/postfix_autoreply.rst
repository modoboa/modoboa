.. _postfix_ar:

###########################
Postfix auto-reply messages
###########################

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
