###################
Create a new plugin
###################

************
Introduction
************

Modoboa offers a plugin API to expand its capabilities. The current
implementation provides the following possibilities:

* Expand navigation by adding entry points to your plugin inside the GUI
* Access and modify administrative objects (domains, mailboxes, etc.)
* Register callback actions for specific events

Plugins are nothing more than Django applications with an extra piece
of code that integrates them into Modoboa. The
:file:`modo_extension.py` file will contain a complete description of
the plugin:

* Admin and user parameters
* Custom menu entries

The communication between both applications is provided by `Django
signals
<https://docs.djangoproject.com/en/1.9/topics/signals/>`_.

The following subsections describe the plugin architecture and explain
how you can create your own.

*****************
The required glue
*****************

To create a new plugin, just start a new django application like
this (into Modoboa's directory)::

  $ python manage.py startapp

Then, you need to register this application using the provided
API. Just copy/paste the following example into the :file:`modo_extension.py` file
of the future extension::

  from modoboa.core.extensions import ModoExtension, exts_pool

  
  class MyExtension(ModoExtension):
      """My custom Modoboa extension."""

      name = "myext"
      label = "My Extension"
      version = "0.1"
      description = "A description"
      url = "myext_root_location" # optional, name is used if not defined
      
      def load(self):
          """This method is called when Modoboa loads available and activated plugins.

          Declare parameters and register events here.
          """ 
          pass
          
      def load_initial_data(self):
          """Optional: provide initial data for your extension here."""
          pass

  exts_pool.register_extension(MyExtension)

Once done, simply add your extension's module name to the
``MODOBOA_APPS`` variable located inside :file:`settings.py`. Finally,
run the following commands::

  $ python manage.py migrate
  $ python manage.py load_initial_data
  $ python manage.py collectstatic

**********
Parameters
**********

A plugin can declare its own parameters. There are two levels available:

* 'Global' parameters : used to configure the plugin, editable
  inside the *Admin > Settings > Parameters* page
* 'User' parameters : per-user parameters (or preferences), editable
  inside the *Options > Preferences* page

Playing with parameters
=======================

Parameters are defined using `Django forms
<https://docs.djangoproject.com/en/1.9/topics/forms/>`_ and Modoboa
adds two special forms you can inherit depending on the level of
parameter(s) you want to add:

* ``modoboa.parameters.forms.AdminParametersForm``: for general parameters

* ``modoboa.parameters.forms.UserParametersForm``: for user parameters

To register new parameters, add the following line into the ``load``
method of your plugin class::

  from modoboa.parameters import tools as param_tools
  param_tools.registry.add(
      LEVEL, YourForm, ugettext_lazy("Title"))

Replace ``LEVEL`` by ``"global"`` or ``"user"``.

***********************
Custom role permissions
***********************

Modoboa uses Django's internal permission system. Administrative roles
are nothing more than groups (``Group`` instances).

An extension can add new permissions to a group by listening to the
``extra_role_permissions`` signal. Here is an example:

.. sourcecode:: python

   from django.dispatch import receiver
   from modoboa.core import signals as core_signals

   PERMISSIONS = {
       "Resellers": [
           ("relaydomains", "relaydomain", "add_relaydomain"),
           ("relaydomains", "relaydomain", "change_relaydomain"),
           ("relaydomains", "relaydomain", "delete_relaydomain"),
           ("relaydomains", "service", "add_service"),
           ("relaydomains", "service", "change_service"),
           ("relaydomains", "service", "delete_service")
       ]
   }

   @receiver(core_signals.extra_role_permissions)
   def extra_role_permissions(sender, role, **kwargs):
      """Add permissions to the Resellers group."""
      return constants.PERMISSIONS.get(role, [])

*********************
Extending admin forms
*********************

The forms used to edit objects (account, domain, etc.) through the admin
panel are composed of tabs. You can extend them (ie. add new
tabs) in a pretty easy way thanks to custom signals.

Account
=======

To add a new tab to the account edition form, define new listeners
(handlers) for the following signals:

* ``modoboa.admin.signals.extra_account_forms``

* ``modoboa.admin.signals.get_account_form_instances``

* ``modoboa.admin.signals.check_extra_account_form`` (optional)

Example:
  
.. sourcecode:: python

   from django.dispatch import receiver
   from modoboa.admin import signals as admin_signals


   @receiver(admin_signals.extra_account_forms)
   def extra_account_form(sender, user, account, **kwargs):
       return [
           {"id": "tabid", "title": "Title", "cls": MyFormClass}
       ]

   @receiver(admin_signals.get_account_form_instances)
   def fill_my_tab(sender, user, account, **kwargs):
       return {"id": my_instance}

       
Domain
======

To add a new tab to the domain edition form, define new listeners
(handlers) for the following signals:

* ``modoboa.admin.signals.extra_domain_forms``

* ``modoboa.admin.signals.get_domain_form_instances``

Example:

.. sourcecode:: python

   from django.dispatch import receiver
   from modoboa.admin import signals as admin_signals


   @receiver(admin_signals.extra_domain_forms)
   def extra_account_form(sender, user, domain, **kwargs):
       return [
           {"id": "tabid", "title": "Title", "cls": MyFormClass}
       ]

   @receiver(admin_signals.get_domain_form_instances)
   def fill_my_tab(sender, user, domain, **kwargs):
       return {"id": my_instance}
