Extending Modoboa
*****************

Introduction
============

Modoboa offers a plugin API to expand its capabilities. The current
implementation provides the following possibilities:

* Expand navigation by adding entry points to your plugin inside the GUI
* Access and modify administrative objects (domains, mailboxes, etc.)
* Register callback actions for specific events

Plugins are nothing more than Django applications with an extra piece
of code that integrates them into Modoboa. Usually, the *__init__.py* file
will contain a complete description of the plugin:

* Admin and user parameters
* Observed events
* Custom menu entries

The communication between both applications is provided by
events. Modoboa offers some kind of hooks to let plugin add custom
actions.

The following subsections describe plugin architecture and explain
how you can create your own plugin.

Adding a custom plugin
======================

To create a new plugin, just start a new django application like
this (into modoboa's directory)::

  $ python manage.py startapp

Then, you need to register this application using the provided
API. Just copy/paste the following example into the *__init__.py* file
of the future extension::

  from modoboa.extensions import ModoExtension, exts_pool
  
  class MyExtension(ModoExtension):
      name = "myext"
      label = "My Extension"
      version = "0.1"
      description = "A description"
      url = "myext_root_location" # optional, name is used if not defined
      
      def init(self):
          """This method is called when the extension is activated.
          """
          pass
          
      def load(self):
          """This method is called when Modoboa loads available and activated plugins.

          Declare parameters and register events here.
          """ 
          pass
          
      def destroy(self):
          """This function is called when a plugin is disabled from the interface.
          
          Unregister parameters and events here.
          """
          pass

  exts_pool.register_extension(MyExtension)

Once done, simply add your plugin's module name to the
``INSTALLED_APPS`` variable located inside *settings.py*. Optionaly,
run ``python manage.py syncdb`` if your plugin provides custom tables
and ``python manage.py collectstatic`` to update static files.

Events
======

Playing with events
-------------------

Modoboa provides a simple API to interact with events. It understands
two kinds of events: 
 
* Those that return a value
* Those that return nothing

Listening to a specific event is achieved as follow::

    from modoboa.lib import events
    
    def callback(*args):
      pass
    
    events.register('event', callback)

You can also use the custom decorator ``events.observe``::

  @events.observe('event')
  def callback(*args):
    pass

``event`` is the event's name you want to listen to, ``callback`` is
the function that will be called each time this event is raised. Each
event impose to callbacks a specific prototype to respect. See below
for a detailled list.

To stop listening to as specific event, you must use the
``unregister`` function::

  events.unregister('event', callback)

The parameters are the same than those used with ``register``.

Read further to get a complete list and description of all available events.

UserLogin
---------

Raised when a user logs in.

*Callback prototype*::

  def callback(request, username, password): pass


UserLogout
----------

Raised when a user logs out.

*Callback prototype*::

  def callback(request): pass


.. _usermenudisplay:

UserMenuDisplay
---------------

Raised when a user menu is about to be displayed. 

*Callback prototype*::

  def callback(target, user): pass

The ``target`` argument indicates which menu is being
displayed. Possible values are:

* ``uprefs_menu`` : corresponds to the menu bar available inside the
  *User preferences* page
* ``top_menu`` : corresponds to the top blue bar

All the callbacks that listen to this event must return a list of
dictionnaries (corresponding to menu entries). Each dictionnary must
contain at least the following keys::

  {"name" : "a_name_without_spaces",
   "label" : _("The menu label"),
   "url" : reverse("your_view"),   # can be set to ""
   "img" : static_url("your_pic")} # can be set to ""

AdminMenuDisplay
----------------

Raised when an admin menu is about to be displayed.

*Callback prototype*::

  def callback(target, user): pass

The ``target`` argument indicates which menu is being
displayed. Possible values are:

* ``admin_menu_box`` : corresponds to the menu bar available inside administration pages
* ``top_menu`` : corresponds to the *Admin* dropdown menu located inside the top blue bar

See :ref:`usermenudisplay` for a description of what callbacks that
listen to this event must return.

GetStaticContent
----------------

Let extensions add static content (ie. CSS or javascript) to default
pages. It is pretty useful for functionalities that don't need a
template but need javascript stuff.

*Callback prototype*::

  def callback(user): pass

* ``user`` is a ``User`` instance corresponding to the currently
  logged in user

Callbacks listening to this event must return a list of string.

CanCreate
---------

Raised just before a user tries to create a new object.

*Callback prototype*::

  def callback(user): pass

* ``user`` is a ``User`` instance

Return ``True`` or ``False`` to indicate if this user can respectively
create or not create a new ``Domain`` object.

CreateDomain
------------

Raised when a new domain is created. 

*Callback prototype*::

  def callback(user, domain): pass

* ``user`` corresponds to the ``User`` object creating the domain (its owner)
* ``domain`` is a ``Domain`` instance

DeleteDomain
------------

Raised when an existing domain is about to be deleted.

*Callback prototype*::

  def callback(domain): pass

* ``domain`` is a ``Domain`` instance

DomainAliasCreated
------------------

Raised when a new domain alias is created.

*Callback prototype*::

  def callback(user, domain_alias): pass

* ``user`` is the new domain alias owner (``User`` instance)
* ``domain_alias`` is the new domain alias (``DomainAlias`` instance)

DomainAliasDeleted
------------------

Raised when an existing domain alias is about to be deleted. 

*Callback prototype*::

  def callback(domain_alias): pass

* ``domain_alias`` is a ``DomainAlias`` instance

CreateMailbox
-------------

Raised when a new mailbox is created.

*Callback prototype*::

  def callback(user, mailbox): pass

* ``user`` is the new mailbox's owner (``User`` instance)
* ``mailbox`` is the new mailbox (``Mailbox`` instance)

DeleteMailbox
-------------

Raised when an existing mailbox is about to be deleted. 

*Callback prototype*::

  def callback(mailbox): pass

* ``mailbox`` is a ``Mailbox`` instance

ModifyMailbox
-------------

Raised when an existing mailbox is modified. 

*Callback prototype*::

  def callback(newmailbox, oldmailbox): pass

* ``newmailbox`` is a ``Mailbox`` instance containing the new values
* ``oldmailbox`` is a ``Mailbox`` instance containing the old values

MailboxAliasCreated
-------------------

Raised when a new mailbox alias is created.

*Callback prototype*::

  def callback(user, mailbox_alias): pass

* ``user`` is the new domain alias owner (``User`` instance)
* ``mailbox_alias`` is the new mailbox alias (``Alias`` instance)

MailboxAliasDeleted
-------------------

Raised when an existing mailbox alias is about to be deleted. 

*Callback prototype*::

  def callback(mailbox_alias): pass

* ``mailbox_alias`` is an ``Alias`` instance

AccountCreated
--------------

Raised when a new account is created.

*Callback prototype*::

  def callback(account): pass

* ``account`` is the newly created account (``User`` instance)


AccountModified
---------------

Raised when an existing account is modified.

*Callback prototype*::

  def callback(oldaccount, newaccount): pass

* ``oldaccount`` is the account before it is modified

* ``newaccount`` is the account after the modification

AccountDeleted
--------------

Raised when an existing account is deleted.

*Callback prototype*::

  def callback(account): pass

* ``oldaccount`` is the account that is going to be deleted

ExtraAccountForm
----------------

Let extensions add new forms to the global account edition form (the
one with tabs).

*Callback prototype*::

  def callback(user, account): pass

* ``user`` is a ``User`` instance corresponding to the currently
  logged in user

* ``account`` is the account beeing modified (``User`` instance)

Callbacks listening to the event must return a list of dictionnaries,
each one must contain at least three keys::

  {"id" : "<the form's id>",
   "title" : "<the title used to present the form>",
   "cls" : TheFormClassName}

CheckExtraAccountForm
---------------------

When an account is being modified, this event lets extensions check if
this account is concerned by a specific form.

*Callback prototype*::

  def callback(account, form): pass

* ``account`` is the ``User`` instance beeing modified

* ``form`` is a dictionnary (same content as for ``ExtraAccountForm``)

Callbacks listening to this event must return a list containing one
Boolean.

FillAccountInstances
--------------------

When an account is beeing modified, this event is raised to fill extra
forms.

*Callback prototype*::

  def callback(user, account, instances): pass

* ``user`` is a ``User`` instance corresponding to the currently
  logged in user

* ``account`` is the ``User`` instance beeing modified

* ``instances`` is a dictionnary where the callback will add
  information needed to fill a specific form

.. _getextraroles:

GetExtraRoles
-------------

Let extensions define new administrative roles.

*Callback prototype*::

  def callback(user): pass

* ``user`` is a ``User`` instance corresponding to the currently
  logged in user

Callbacks listening to this event must return a list of 2uple (two
strings) which respect the following format: ``(value, label)``.

ExtEnabled
----------

Raised just after an extension has been activated. 

*Callback prototype*::

  def callback(extension): pass

* ``extension`` is an ``Extension`` instance

ExtDisabled
-----------

Raised just after an extension has been disabled. 

*Callback prototype*::

  def callback(extension): pass

* ``extension`` is an ``Extension`` instance

GetAnnouncement
---------------

Some places in the interface let plugins add their own announcement
(ie. message). 

*Callback prototype*::

  def callback(target): pass

* ``target`` is a string indicating the place where the announcement
  will appear:

* ``loginpage`` : corresponds to the login page

Callbacks listening to this event must return a list of string.

TopNotifications
----------------

Let extensions add custom content into the top bar.

*Callback prototype*::

  def callback(user): pass

* ``user`` is a ``User`` instance corresponding to the currently
  logged in user

Callbacks listening to this event must return a list of string.

ExtraAdminContent
-----------------

Let extensions add extra content into the admin panel.

*Callback prototype*::

  def callback(user, target, currentpage): pass

* ``user`` is a ``User`` instance corresponding to the currently
  logged in user

* ``target`` is a string indicating the place where the content will
  be displayed. Possible values are : ``leftcol``

* ``currentpage`` is a string indicating which page (or section) is
  displayed. Possible values are : ``domains``, ``identities``

Callbacks listening to this event must return a list of string.

PasswordChange
--------------

Raised just before a *password change* action. 

*Callback prototype*::

  def callback(user): pass

* ``user`` is a ``User`` instance

Callbacks listening to this event must return a list containing either
``True`` or ``False``. If at least one ``True`` is returned, the
*password change* will be cancelled (ie. changing the password for
this user is disabled).

Parameters
==========

A plugin can declare its own parameters. There are two levels available:

* 'Administration' parameters : used to configure the plugin, editable
  inside the *Admin > Settings > Parameters* page,
* 'User' parameters : per-user parameters (or preferences), editable
  inside the *Options > Preferences* page.

Playing with parameters
-----------------------

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

To undeclare parameters (for example when a plugin is disabled is
disabled from the interface), use the following function::

  parameters.unregister_app(appname)

``appname`` corresponds to your plugin's name, ie. the name of the
directory containing the source code.

Custom administrative roles
===========================

Modoboa uses Django's internal permission system. Administrative roles
are nothing more than groups (``Group`` instances).

If an extension needs to add new roles, it needs to follow those steps:

#. Create a new ``Group`` instance. It can be done by providing
   `fixtures <https://docs.djangoproject.com/en/dev/howto/initial-data/>`_ 
   or by creating it into the extension ``init`` function

#. A a new listener for the :ref:`getextraroles` event that will return
   the group's name
