Extending Modoboa
*****************

Introduction
============

Modoboa offers a plugin API to expand its capabilities. The current
implementation provides the following possibilities:

* Expand navigation by adding entry points to your plugin inside the GUI
* Access and modify administrative objects (domains, mailboxes, etc.)
* Register callback actions for specific events

Plugins are nothing more than Django applications using a specific
structure. The ``__init__.py`` file contains a complete description of
the plugin:

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

All Modoboa plugins must be located inside the ``extensions``
directory. To create a new plugin, execute the following steps:

* Run ``python manage.py startapp`` to get some basefiles for your plugin
* Move the resulting directory inside the ``extensions`` one

The ``__init__.py`` file created inside your module's directory must
follow a specific structure in order to be interpreted by Modoboa. The
following functions are mandatory::

  def init():
    """This function is called when the extension is activated.
    """
    pass

  def load():
    """This function is called when Modoboa loads available and activated plugins.

    Declare parameters and register events here.
    """ 
    pass

  def destroy():
    """This function is called when a plugin is disabled from the interface.

    Unregister parameters and events here.
    """
    pass

  def infos():
    """This function is used to populate the plugins list 
    available in the administration panel.

    It must return a dictionnary containing at least three 
    keys : "name", "version", "description"
    """
    return {
        "name" : "Example plugin",
	"version" : "1.0",
	"description" : "Example description"
        }

Once you have filled ``__init__.py``, simply add your plugin's name to
the ``INSTALLED_APPS`` variable located inside ``settings.py``. (use
the same format as other plugins). Eventually, run ``python manage.py
syncdb`` if your plugin provides custom tables.

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

AdminFooterDisplay
------------------

Raised when the footer (ie. bottom of the page) of listing pages
inside the ``admin`` application is displayed. Plugins can listen to
this event when they want to add specific information into that place.

*Callback prototype*::

  def callback(user, object_type): pass

* ``user`` is a ``User`` instance (the one that is displaying the page)
* ``object_type`` is a string indicating which kind of object is
  displayed. Possible values are:

 * ``domains``: a list of domains
 * ``domaliases``: a list of domain aliases
 * ``mailboxes``: a list of mailboxes
 * ``mbaliases``: a list of mailbox aliases

Registered callbacks must return a list of string objects.

CanCreateDomain
---------------

Raised just before a user tries to access the ``newdomain`` function.

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

CanCreateDomainAlias
--------------------

Raised just before a user tries to access the ``newdomalias`` function.

*Callback prototype*::

  def callback(user): pass

* ``user`` is a ``User`` instance

Return ``True`` or ``False`` to indicate that the user can
respectively create or not create a new domain alias.

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

CanCreateMailbox
----------------

Raised just before a user tries to access the ``newmailbox`` function.

*Callback prototype*::

  def callback(user): pass

* ``user`` is a ``User`` instance

Return ``True`` or ``False`` to indicate that the user can
respectively create or not create a new mailbox.

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

CanCreateMailboxAlias
---------------------

Raised just before a user tries to access the ``newmbalias`` function.

*Callback prototype*::

  def callback(user): pass

* ``user`` is a ``User`` instance

Return ``True`` or ``False`` to indicate that the user can
respectively create or not create a new mailbox alias.

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

.. _permsgettables:

PermsGetTables
--------------

Raised when the different permission lists (one per role) are about to
be displayed. 

*Callback prototype*::

  def callback(request): pass

* ``request`` is a ``Request`` instance

Callbacks that listen to this event must return a list of
dictionnaries (corresponding to tables). Each dictionnary must contain
at least the following elements::

  {"id" : "table_id",
   "title" : _("The title corresponding to this table"),
   "rel" : "x y",
   "content" : MyPermClass().get(request)}

For ``rel``, replace x and y with the *Add form* size (the one that
appears when you click on the ``Add permission`` button.

For ``content``, replace *MyPermClass* with the appropriate name.

.. _permsgetclass:

PermsGetClass
-------------

Raised to retrieve the class (inheriting from ``Permissions``)
implementing a specific role. This event is used to add or delete or
new instance of this role. 

*Callback prototype*::

  def callback(role): pass

* ``role`` is a string indicating the role beeing added

Callbacks listening to this event must return the class object
corresponding to the given ``role`` argument.

SuperAdminPromotion
-------------------

Raised when an existing user becomes a super administrator. Each group
that user belongs to is still available (inside the ``user.groups``
queryset) at the time the event is raised.

*Callback prototype*::

  def callback(user): pass

* ``user`` is a ``User`` instance

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

Custom permission levels
========================

Custom permissions roles can be added to Modoboa. If you to want to
integrate the default permissions panel (*Admin > Permissions*), each
role you add must inherit from the ``Permissions`` class (see file
``admin/permissions.py``) and implement all its methods.

.. note::
   See :ref:`permsgettables` and :ref:`permsgetclass` to learn how to
   integrate your custom roles.


