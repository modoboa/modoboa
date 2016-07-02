###################
Adding a new plugin
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
of code that integrates them into Modoboa. The *modo_extension.py* file
will contain a complete description of the plugin:

* Admin and user parameters
* Observed events
* Custom menu entries

The communication between both applications is provided by
:ref:`events`. Modoboa offers some kind of hooks to let plugin add custom
actions.

The following subsections describe plugin architecture and explain
how you can create your own plugin.

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

* 'Administration' parameters : used to configure the plugin, editable
  inside the *Admin > Settings > Parameters* page,
* 'User' parameters : per-user parameters (or preferences), editable
  inside the *Options > Preferences* page.

Playing with parameters
=======================

To declare a new administration parameter, use the following function::

  from modoboa.lib import parameters

  parameters.register_admin(name, **kwargs)

To declare a new user parameter, use the following function::

  parameter.register_user(name, **kwargs)

Both functions accept extra arguments listed here:

* ``type`` : parameter's type, possible values are : ``int``, ``string``, ``list``, ``list_yesno``,
* ``deflt`` : default value,
* ``help`` : help text,
* ``values`` : list of possible values if ``type`` is ``list``.

***************************
Custom administrative roles
***************************

Modoboa uses Django's internal permission system. Administrative roles
are nothing more than groups (``Group`` instances).

If an extension needs to add new roles, the following steps are required:

#. Listen to the :ref:`getextraroles` event that will return
   the group's name

#. Listen to the :ref:`getextrarolepermissions` event that will return
   the new group's permissions

The group will automatically be created the next time you run the
``load_initial_data`` command.

*********************
Extending admin forms
*********************

the forms used to edit objects (account, domain, etc.) through the admin
panel are composed of tabs. You can extend those forms (ie. add new
tabs) in a pretty easy way by defining events.

Account
=======

To add a new tab to the account edition form, define new listeners
(handlers) for the following events:

* :ref:`event_extraaccountform`

* :ref:`event_fillaccountinstances`

* :ref:`event_checkextraaccountform` (optional)

Example:
  
.. sourcecode:: python

   from modoboa.lib import events

   @events.observe("ExtraAccountForm")
   def extra_account_form(user, account=None):
       return [
           {"id": "tabid", "title": "Title", "cls": MyFormClass}
       ]

   @events.observe("FillAccountInstances")
   def fill_my_tab(user, account, instances):
       instances["id"] = my_instance
       
       
Domain
======

To add a new tab to the domain edition form, define new listeners
(handlers) for the following events:

* :ref:`event_extradomainform`

* :ref:`event_filldomaininstances`

Example:

.. sourcecode:: python

   from modoboa.lib import events

   @events.observe("ExtraDomainForm")
   def extra_domain_form(user, domain):
       return [
           {"id": "tabid", "title": "Title", "cls": MyFormClass}
       ]

   @events.observe("FillDomainInstances")
   def fill_my_tab(user, domain, instances):
       instances["id"] = my_instance
