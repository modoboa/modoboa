.. _events:

################
Available events
################

************
Introduction
************

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

****************
Supported events
****************

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

  def callback(account): pass

* ``oldaccount`` is the account that is going to be deleted
  
AccountModified
===============

Raised when an existing account is modified.

*Callback prototype*::

  def callback(oldaccount, newaccount): pass

* ``oldaccount`` is the account before it is modified

* ``newaccount`` is the account after the modification

ExtraAccountActions
===================

Raised when the account list is displayed. Let developers define new
actions to act on a specific user.

*Callback prototype*::

  def callback(account): pass

* ``account`` is the account being listed

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

CanCreate
=========

Raised just before a user tries to create a new object.

*Callback prototype*::

  def callback(user): pass

* ``user`` is a ``User`` instance

Return ``True`` or ``False`` to indicate if this user can respectively
create or not create a new ``Domain`` object.

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

CreateDomain
============

Raised when a new domain is created. 

*Callback prototype*::

  def callback(user, domain): pass

* ``user`` corresponds to the ``User`` object creating the domain (its owner)
* ``domain`` is a ``Domain`` instance

CreateMailbox
=============

Raised when a new mailbox is created.

*Callback prototype*::

  def callback(user, mailbox): pass

* ``user`` is the new mailbox's owner (``User`` instance)
* ``mailbox`` is the new mailbox (``Mailbox`` instance)

DeleteDomain
============

Raised when an existing domain is about to be deleted.

*Callback prototype*::

  def callback(domain): pass

* ``domain`` is a ``Domain`` instance

DeleteMailbox
=============

Raised when an existing mailbox is about to be deleted. 

*Callback prototype*::

  def callback(mailbox): pass

* ``mailbox`` is a ``Mailbox`` instance

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

DomainModified
==============

Raised when a domain has been modified.

*Callback prototype*::

  def callback(domain): pass

* ``domain`` is the modified ``Domain`` instance, it contains an extra
  ``oldname`` field which contains the old domain name

ExtDisabled
===========

Raised just after an extension has been disabled. 

*Callback prototype*::

  def callback(extension): pass

* ``extension`` is an ``Extension`` instance

ExtEnabled
==========

Raised just after an extension has been activated. 

*Callback prototype*::

  def callback(extension): pass

* ``extension`` is an ``Extension`` instance

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

.. _getextraroles:

GetExtraRoles
=============

Let extensions define new administrative roles.

*Callback prototype*::

  def callback(user): pass

* ``user`` is a ``User`` instance corresponding to the currently
  logged in user

Callbacks listening to this event must return a list of 2uple (two
strings) which respect the following format: ``(value, label)``.

GetStaticContent
================

Let extensions add static content (ie. CSS or javascript) to default
pages. It is pretty useful for functionalities that don't need a
template but need javascript stuff.

*Callback prototype*::

  def callback(user): pass

* ``user`` is a ``User`` instance corresponding to the currently
  logged in user

Callbacks listening to this event must return a list of string.

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

ModifyMailbox
=============

Raised when an existing mailbox is modified. 

*Callback prototype*::

  def callback(newmailbox, oldmailbox): pass

* ``newmailbox`` is a ``Mailbox`` instance containing the new values
* ``oldmailbox`` is a ``Mailbox`` instance containing the old values

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

Let extensions add custom content into the top bar.

*Callback prototype*::

  def callback(user): pass

* ``user`` is a ``User`` instance corresponding to the currently
  logged in user

Callbacks listening to this event must return a list of string.

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
