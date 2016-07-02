.. _events:

################
Available events
################

************
Introduction
************

Modoboa provides a simple API to interact with events. It understands
two kinds of events: 
 
* Those returning a value
* Those returning nothing

Listening to a specific event is achieved as follows::

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

To unregister all events declared by a specific extension, use the
``unregister_extension`` function::

  events.unregister_extension([name])

``name`` is the extension's name but it is optional. Leave it empty to
let the function guess the name.

Read further to get a complete list and description of all available events.

****************
Supported events
****************

AccountAutoCreated
==================

Raised when a new account is automatically created (example: LDAP
synchronization).

*Callback prototype*::

  def callback(account): pass

* ``account`` is the newly created account (``User`` instance)

AccountCreated
==============

Raised when a new account is created.

*Callback prototype*::

  def callback(account): pass

* ``account`` is the newly created account (``User`` instance)

AccountDeleted
==============

Raised when an existing account is deleted.

*Callback prototype*::

  def callback(account, byuser, **options): pass

* ``account`` is the account that is going to be deleted
* ``byuser`` is the adminstrator deleting ``account``

AccountExported
===============

Raised when an account is exported to CSV.

*Callback prototype*::

  def callback(account): pass

* ``account`` is the account being exported

Must return a list of values to include in the export.

AccountImported
===============

Raised when an account is imported from CSV.

*Callback prototype*::

  def callback(user, account, row): pass

* ``user`` is the user importing the account
* ``account`` is the account being imported
* ``row`` is a list containing what remains from the CSV definition
  
AccountModified
===============

Raised when an existing account is modified.

*Callback prototype*::

  def callback(oldaccount, newaccount): pass

* ``oldaccount`` is the account before it is modified

* ``newaccount`` is the account after the modification

AdminMenuDisplay
================

Raised when an admin menu is about to be displayed.

*Callback prototype*::

  def callback(target, user): pass

The ``target`` argument indicates which menu is being
displayed. Possible values are:

* ``admin_menu_box`` : corresponds to the menu bar available inside administration pages
* ``top_menu`` : corresponds to the top black bar

See :ref:`usermenudisplay` for a description of what callbacks that
listen to this event must return.

CheckDomainName
===============

Raised before the unicity of a domain name is checked. By default,
modoboa prevents duplicate names between domains and domain aliases
but extensions have the possibility to extend this rule using this
event.

*Callback prototype*::

  def callback(): pass

Must return a list of 2uple, each one containing a model class and an
associated label.

.. _event_checkextraaccountform:

CheckExtraAccountForm
=====================

When an account is being modified, this event lets extensions check if
this account is concerned by a specific form.

*Callback prototype*::

  def callback(account, form): pass

* ``account`` is the ``User`` instance beeing modified

* ``form`` is a dictionnary (same content as for ``ExtraAccountForm``)

Callbacks listening to this event must return a list containing one
Boolean.

DomainAliasCreated
==================

Raised when a new domain alias is created.

*Callback prototype*::

  def callback(user, domain_alias): pass

* ``user`` is the new domain alias owner (``User`` instance)
* ``domain_alias`` is the new domain alias (``DomainAlias`` instance)

DomainAliasDeleted
==================

Raised when an existing domain alias is about to be deleted. 

*Callback prototype*::

  def callback(domain_alias): pass

* ``domain_alias`` is a ``DomainAlias`` instance

DomainCreated
=============

Raised when a new domain is created. 

*Callback prototype*::

  def callback(user, domain): pass

* ``user`` corresponds to the ``User`` object creating the domain (its owner)
* ``domain`` is a ``Domain`` instance

DomainDeleted
=============

Raised when an existing domain is about to be deleted.

*Callback prototype*::

  def callback(domain): pass

* ``domain`` is a ``Domain`` instance

DomainModified
==============

Raised when a domain has been modified.

*Callback prototype*::

  def callback(domain): pass

* ``domain`` is the modified ``Domain`` instance, it contains an extra
  ``oldname`` field which contains the old name

DomainOwnershipRemoved
======================

Raised before the ownership of a domain is removed from its original
creator.

*Callback prototype*::

  def callback(owner, domain): pass

* ``owner`` is the original creator
* ``domain`` is the ``Domain`` instance being modified

ExtraAccountActions
===================

Raised when the account list is displayed. Let developers define new
actions to act on a specific user.

*Callback prototype*::

  def callback(account): pass

* ``account`` is the account being listed

.. _event_extraaccountform:
  
ExtraAccountForm
================

Let extensions add new forms to the account edition form (the one with
tabs).

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

ExtraAdminContent
=================

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

ExtraDomainEntries
==================

Raised to request extra entries to display inside the *domains*
listing.

*Callback prototype*::

  def callback(user, domfilter, searchquery, **extrafilters): pass

* ``user`` is the ``User`` instance corresponding to the currently
  logged in user
* ``domfilter`` is a string indicating which domain type the user needs
* ``searchquery`` is a string containing a search query
* ``extrafilters`` is a set of keyword arguments that may contain additional filters

Must return a valid ``QuerySet``.

ExtraDomainFilters
==================

Raised to request extra filters for the *domains* listing page. For
example, the *postfix_relay_domains* extension let users filter
entries based on service types.

*Callback prototype*::

  def callback(): pass

Must return a list of valid filter names (string).

.. _event_extradomainform:

ExtraDomainForm
===============

Let extensions add new forms to the domain edition form (the one with
tabs).

*Callback prototype*::

  def callback(user, domain): pass

* ``user`` is a ``User`` instance corresponding to the currently
  logged in user

* ``domain`` is the domain beeing modified (``Domain`` instance)

Callbacks listening to the event must return a list of dictionnaries,
each one must contain at least three keys::

  {"id" : "<the form's id>",
   "title" : "<the title used to present the form>",
   "cls" : TheFormClassName}

ExtraDomainImportHelp
=====================

Raised to request extra help text to display inside the domain import
form.

*Callback prototype*::

  def callback(): pass

Must return a list a string.

ExtraDomainMenuEntries
======================

Raised to request extra entries to include in the left menu of the
*domains* listing page.

*Callback prototype*::

  def callback(user): pass

* ``user`` is the ``User`` instance corresponding to the currently
  logged in user

Must return a list of dictionaries. Each dictionary must contain at
least three keys::

  {"name": "<menu name>",
   "label": "<menu label>",
   "url": "<menu url>"}

.. _extraformfields:

ExtraFormFields
===============

Raised to request extra fields to include in a django form.

*Callback prototype*::

  def callback(form_name, instance=None): pass

* ``form_name`` is a string used to distinguish a specific form
* ``instance`` is a django model instance related to ``form_name``

Must return a list of 2uple, each one containing the following
information::

  ('field name', <Django form field instance>)

ExtraRelayDomainForm
====================

Let extensions add new forms to the relay domain edition form (the one
with tabs).

*Callback prototype*::

  def callback(user, rdomain): pass

* ``user`` is the ``User`` instance corresponding to the currently
  logged in user
* ``rdomain`` is the relay domain being modified (``RelayDomain`` instance)

Callbacks listening to the event must return a list of dictionnaries,
each one must contain at least three keys::

  {"id" : "<the form's id>",
   "title" : "<the title used to present the form>",
   "cls" : TheFormClassName}

.. _event_fillaccountinstances:
   
FillAccountInstances
====================

When an account is beeing modified, this event is raised to fill extra
forms.

*Callback prototype*::

  def callback(user, account, instances): pass

* ``user`` is a ``User`` instance corresponding to the currently
  logged in user

* ``account`` is the ``User`` instance beeing modified

* ``instances`` is a dictionnary where the callback will add
  information needed to fill a specific form

.. _event_filldomaininstances:
  
FillDomainInstances
===================

When a domain is beeing modified, this event is raised to fill extra
forms.

*Callback prototype*::

  def callback(user, domain, instances): pass

* ``user`` is a ``User`` instance corresponding to the currently
  logged in user

* ``domain`` is the ``Domain`` instance beeing modified

* ``instances`` is a dictionnary where the callback will add
  information needed to fill a specific form

FillRelayDomainInstances
========================

When a relay domain is being modified, this event is raised to fill extra
forms.

*Callback prototype*::

  def callback(user, rdomain, instances): pass

* ``user`` is the ``User`` instance corresponding to the currently
  logged in user

* ``rdomain`` is the ``RelayDomain`` instance being modified

* ``instances`` is a dictionnary where the callback will add
  information needed to fill a specific form

GetAnnouncement
===============

Some places in the interface let plugins add their own announcement
(ie. message). 

*Callback prototype*::

  def callback(target): pass

* ``target`` is a string indicating the place where the announcement
  will appear:

* ``loginpage`` : corresponds to the login page

Callbacks listening to this event must return a list of string.

GetDomainActions
================

Raised to request the list of actions available for the *domains*
listing entry being displayed.

*Callback prototype*::

  def callback(user, rdomain): pass

* ``user`` is the ``User`` instance corresponding to the currently
  logged in user
* ``rdomain`` is the ``RelayDomain`` instance being displayed

Must return a list of dictionaries, each dictionary containing at
least the following entries::

  {"name": "<action name>",
   "url": "<action url>",
   "title": "<action title>",
   "img": "<action icon>"}

GetDomainModifyLink
===================

Raised to request the modification url of the *domains* listing entry
being displayed.

*Callback prototype*::

  def callback(domain): pass

* ``domain`` is a model instance (``RelayDomain`` for example)

Must return a dictionary containing at least the following entry::

  {'url': '<modification url>'}

GetExtraLimitTemplates
======================

Raised to request extra limit templates. For example, the
*postfix_relay_domains* extension define a template to limit the
number of relay domains an administrator can create.

*Callback prototype*::

  def callback(): pass

Must return a list of set. Each set must contain at least three entries::

  [('<limit_name>', '<limit label>', '<limit help text>')]

GetExtraParameters
==================

Raised to request extra parameters for a given parameters form.

*Callback prototype*::

  def callback(application, level): pass

* ``application`` is the name of the form's application (ie. admin, amavis, etc.)
* ``level`` is the form's level: ``A`` for admin or ``U`` for user

Must return a dictionary. Each entry must be a valid Django form field.

.. _getextrarolepermissions:

GetExtraRolePermissions
=======================

Let extensions define new permissions for a given role.

*Callback prototype*::

  def callback(rolename): pass

* ``rolename`` is the role's name (str)

Callbacks listening to this event must return a list of list. The
second list level must contain exactly 3 strings: the application
name, the model name and the permission name. Example::

    [
        ["core", "user", "add_user"],
        ["core", "user", "change_user"],
        ["core", "user", "delete_user"],
    ]

.. _getextraroles:

GetExtraRoles
=============

Let extensions define new administrative roles (will be used to create
or modify an account).

*Callback prototype*::

  def callback(user, account): pass

* ``user`` is a ``User`` instance corresponding to the currently
  logged in user
* ``account`` is the account being modified (None on creation)

Callbacks listening to this event must return a list of 2uple (two
strings) which respect the following format: ``(value, label)``.

GetStaticContent
================

Let extensions add static content (ie. CSS or javascript) to default
pages. It is pretty useful for functionalities that don't need a
template but need javascript stuff.

*Callback prototype*::

  def callback(caller, st_type, user): pass

* ``caller`` is name of the application (or the location) responsible
  for the call

* ``st_type`` is the expected static content type (``css`` or ``js``)

* ``user`` is a ``User`` instance corresponding to the currently
  logged in user

Callbacks listening to this event must return a list of string.

ImportObject
============

Raised to request the function handling an object being imported from CSV.

*Callback prototype*::

  def callback(objtype): pass

``objtype`` is the type of object being imported

Must return a list of function. A valid import function must respect
the following prototype::

  def import_function(user, row, formopts): pass

* ``user`` is the ``User`` instance corresponding to the currently
  logged in user
* ``row`` is a string containing the object's definition (CSV format)
* ``formopts`` is a dictionary that may contain options

InitialDataLoaded
=================

Raised a initial data has been loaded for a given extension.

*Callback prototype*::

  def callback(extname); pass

 ``extname`` is the extension name (str)

MailboxAliasCreated
===================

Raised when a new mailbox alias is created.

*Callback prototype*::

  def callback(user, mailbox_alias): pass

* ``user`` is the new domain alias owner (``User`` instance)
* ``mailbox_alias`` is the new mailbox alias (``Alias`` instance)

MailboxAliasDeleted
===================

Raised when an existing mailbox alias is about to be deleted. 

*Callback prototype*::

  def callback(mailbox_alias): pass

* ``mailbox_alias`` is an ``Alias`` instance

MailboxCreated
==============

Raised when a new mailbox is created.

*Callback prototype*::

  def callback(user, mailbox): pass

* ``user`` is the new mailbox's owner (``User`` instance)
* ``mailbox`` is the new mailbox (``Mailbox`` instance)

MailboxDeleted
==============

Raised when an existing mailbox is about to be deleted. 

*Callback prototype*::

  def callback(mailbox): pass

* ``mailbox`` is a ``Mailbox`` instance

MailboxModified
===============

Raised when an existing mailbox is modified. 

*Callback prototype*::

  def callback(mailbox): pass

* ``mailbox`` is the ``Mailbox`` modified instance. It contains a
  ``old_full_address`` extra field to check if the address was
  modified.

PasswordChange
==============

Raised just before a *password change* action. 

*Callback prototype*::

  def callback(user): pass

* ``user`` is a ``User`` instance

Callbacks listening to this event must return a list containing either
``True`` or ``False``. If at least one ``True`` is returned, the
*password change* will be cancelled (ie. changing the password for
this user is disabled).

TopNotifications
================

Lets extensions subscribe to the global notification service (located
inside the top bar).

*Callback prototype*::

  def callback(user, include_all): pass

* ``request`` is a ``Request`` instance
* ``include_all`` is a boolean indicating if empty notifications must
  be included into the result or not

Callbacks listening to this event must return a list of dictionary,
each dictionary containing at least the following entries::

  {"id": "<notification entry ID>",
   "url": "<associated URL>",
   "text": "<text to display>"}

If your notification needs a counter, you can specify it by adding the
two following entries in the dictionary:

  {"counter": <associated counter>,
   "level": "<info|success|warning|error>"}

UserLogin
=========

Raised when a user logs in.

*Callback prototype*::

  def callback(request, username, password): pass

UserLogout
==========

Raised when a user logs out.

*Callback prototype*::

  def callback(request): pass

.. _usermenudisplay:

UserMenuDisplay
===============

Raised when a user menu is about to be displayed. 

*Callback prototype*::

  def callback(target, user): pass

The ``target`` argument indicates which menu is being
displayed. Possible values are:

* ``options_menu``: corresponds to the top-right user menu
* ``uprefs_menu``: corresponds to the menu bar available inside the
  *User preferences* page
* ``top_menu``: corresponds to the top black bar

All the callbacks that listen to this event must return a list of
dictionnaries (corresponding to menu entries). Each dictionnary must
contain at least the following keys::

  {"name" : "a_name_without_spaces",
   "label" : _("The menu label"),
   "url" : reverse("your_view")}

RelayDomainAliasCreated
=======================

Raised when a new relay domain alias is created.

*Callback prototype*::

  def callback(user, rdomain_alias): pass

* ``user`` is the new relay domain alias owner (``User`` instance)
* ``rdomain_alias`` is the new relay domain alias (``DomainAlias`` instance)

RelayDomainAliasDeleted
=======================

Raised when an existing relay domain alias is about to be deleted. 

*Callback prototype*::

  def callback(rdomain_alias): pass

* ``rdomain_alias`` is a ``RelayDomainAlias`` instance

RelayDomainCreated
==================

Raised when a new relay domain is created.

*Callback prototype*::

  def callback(user, rdomain): pass

* ``user`` corresponds to the ``User`` object creating the relay domain (its owner)
* ``rdomain`` is a ``RelayDomain`` instance

RelayDomainDeleted
==================

Raised when an existing relay domain is about to be deleted.

*Callback prototype*::

  def callback(rdomain): pass

* ``rdomain`` is a ``RelayDomain`` instance

RelayDomainModified
===================

Raised when a relay domain has been modified.

*Callback prototype*::

  def callback(rdomain): pass

* ``rdomain`` is the modified ``RelayDomain`` instance, it contains an
   extra ``oldname`` field which contains the old name

RoleChanged
===========

Raised when the role of an account is about to be changed.

*Callback prototype*::

  def callback(account, role): pass

* ``account`` is the account being modified
* ``role`` is the new role (string)

SaveExtraFormFields
===================

Raised to save extra fields declared using :ref:`extraformfields`.

*Callback prototype*::

  def callback(form_name, instance, values): pass

* ``form_name`` is a string used to distinguish a specific form
* ``instance`` is a django model instance related to ``form_name``
* ``values`` is a dictionary containing the form's values

UserCanSetRole
==============

Raised to check if a user is allowed to set a given role to an
account.

*Callback prototype*::

  def callback(user, role, account): pass

* ``user`` is the ``User`` instance corresponding to the currently
  logged in user
* ``role`` is the role ``user`` tries to set
* ``account`` is the account being modified (None on creation)

Must return a list containing ``True`` or ``False`` to indicate if
this user can is allowed to set ``role``.
