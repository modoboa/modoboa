#################
Radicale frontend
#################

This plugin provides a simple management frontend for `Radicale
<http://radicale.org/>`_, a complete CalDAV (calendar) and CardDAV
(contact) server solution.

Features currently supported are:

* Private calendar creation (available for simple users)
* Rights management for private calendars
* Shared calendar creation by domain (available for domain administrators)

.. note::

   This plugin requires Radicale 0.9 or higher.

Setup
=====

Once `Radicale is installed
<http://radicale.org/user_documentation/>`_ on your server, you must
tell Modoboa where it can find the file used to store rules.

Go to the *Modoboa > Parameters > Radicale* panel and fill the
**Radicale rights file path** setting (an absolute path is required).

When the configuration is done, Modoboa will completly handles the
file's content. It means every manual modification you could made on
this file would be overriden.

To do so, a new cron job must be created. You can use the following
example::

  */2 * * * * <modoboa_site>/manage.py generate_rights
  #
  # Or like this if you use a virtual environment:
  # */2 * * * * <virtualenv path/bin/python> <modoboa_site>/manage.py generate_rights

.. note::

   In some cases, the modifications you make on Modoboa may not be
   applied to the rights file. In order to force the generation,
   manually run the ``generate_rights`` command using the ``--force``
   option.
