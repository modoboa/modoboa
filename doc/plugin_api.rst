Extending Modoboa
=================

Introduction
------------

Modoboa tries to be modular. In other words, Modoboa is a collection
of different applications that work with each other, sharing the same
interface. For now, you can see Modoboa as a placeholder for your
plugin.

In a perfect world, adding a feature to Modoboa results in adding a
new plugin. This is currently the case (almost...) and should continue
like this.

The current API is really simple. You have the possibility to:
 * Create entry points to your plugin inside the GUI,
 * Modify administration objects (domains, mailboxes, etc.), 
 * Be notified of specific events.

With that, you can develop pretty advanced applications but we know
(Modoboa's team) it is not enough. For example, you can't create a
*Contacts* plugin that will work with the *Webmail* one.

The API needs to be improved and it will be done with future releases
so stay tuned :-).

How Modoboa and plugins communicate together
--------------------------------------------

Modoboa plugins are actually Django applications but with an extra file
called ``main.py``. This file contains a complete description of the
plugin:

 * Admin and user parameters
 * Registered events
 * Menus

According to that, a plugin can integrate Modoboa in different ways:
 * Extend the usual menus by adding custom entries, they will provide direct access to the plugin core content,
 * Add custom actions called when specific events are raised.

Adding a custom plugin
----------------------

All Modoboa plugins must be located inside the ``extensions``
directory. To create a new plugin, execute the following steps:

 * Run ``python manage.py startapp`` to get some basefiles for your plugin,
 * Move the resulting directory inside the ``extensions`` one,
 * Create a file called ``main.py`` inside your plugin's directory.

The last file you created must follow a specific structure in order to
be interpreted by Modoboa. The following functions are mandatory::

  def init():
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

  def urls(prefix):
    """This function is used to update the global urls table.

    It must return a sequence that corresponds to those used 
    inside the main ``urls.py`` file. (ie. a classical 
    Django construction)

    :param prefix: the global url prefix (the part after the hostname)
    """
    return (r'^%sexample/' % prefix, include('modoboa.extensions.example.urls'))

Once you have filled ``main.py``, simply add your plugin's name to the
``INSTALLED_APPS`` variable located inside ``settings.py``. (use the
same format as other plugins). Eventually, run ``python manage.py
syncdb`` if your plugin provides custom tables.

Events
------

Playing with events
^^^^^^^^^^^^^^^^^^^

Modoboa provides a simple API to interact with events. It understands
two kinds of events: 
 
 * Those that return a value,
 * Those that return nothing.

Listening to a specific event is achieved as follow::

  from modoboa.lib import events

  events.register(event, callback)

``event`` is the event's name you want to listen to, ``callback`` is
the function that will be called when this event is raised. Its
prototype must be as follow::

  def callback(*args, **kwargs):
    pass

It is very generic, it allows events to provide arguments if needed.

You can also stop listening to an event like this::

  events.unregister(event, callback)

The parameters are the same as those used with ``register``.

Read further to get a complete list and description of the available events.

UserLogin
^^^^^^^^^

Raised when a user logs in. This event provides a ``request`` argument
that corresponds to the ``Request`` object used inside the associated
view function.

UserLogout
^^^^^^^^^^

Raised when a user logs out. This event provides a ``request`` argument
that corresponds to the ``Request`` object used inside the associated
view function.

.. _usermenudisplay:

UserMenuDisplay
^^^^^^^^^^^^^^^

Raised when a user menu is about to be displayed. It provides a
``target`` argument that indicates which menu is being
displayed. Possible values are:

 * ``uprefs_menu`` : corresponds to the menu bar available inside the *User preferences* page
 * ``top_menu`` : corresponds to the top blue bar

All callbacks that listen to this event must return a list of
dictionnaries (corresponding to menu entries). Each dictionnary must
contain at least the following keys::

  {"name" : "a_name_without_spaces",
   "label" : _("The menu label"),
   "url" : reverse("your_view"),   # can be set to ""
   "img" : static_url("your_pic")} # can be set to ""

AdminMenuDisplay
^^^^^^^^^^^^^^^^

Raised when an admin menu is about to be displayed. It provides a
``target`` argument that indicates which menu is being
displayed. Possible values are:

 * ``admin_menu_box`` : corresponds to the menu bar available inside administration pages
 * ``top_menu`` : corresponds to the *Admin* dropdown menu located inside the top blue bar

See :ref:`usermenudisplay` for a description of what callbacks that
listen to this event must return.

CreateDomain
^^^^^^^^^^^^

Raised when a new domain is created. The new domain object is
available inside the ``dom`` argument.

DeleteDomain
^^^^^^^^^^^^

Raised when an existing domain is about to be deleted. The domain
object is available inside the ``dom`` argument.

CreateMailbox
^^^^^^^^^^^^^

Raised when a new mailbox is created. The new mailbox object is
available inside the ``mbox`` argument.

DeleteMailbox
^^^^^^^^^^^^^

Raised when an existing mailbox is about to be deleted. The mailbox
object is available inside the ``mbox`` argument.

ModifyMailbox
^^^^^^^^^^^^^

Raised when an existing mailbox is modified. The old mailbox and the
new mailbox objects are respectively available inside the ``oldmbox``
and ``mbox`` arguments.

.. _permsgettables:

PermsGetTables
^^^^^^^^^^^^^^

Raised when the different permission lists (one per role) are about to
be displayed. The current *User* object is available inside the
``user`` argument.

Callbacks that listen to this event must return a list of
dictionnaries (corresponding to tables). Each dictionnary must contain
at least the following elements::

  {"id" : "table_id",
   "title" : _("The title corresponding to this table"),
   "rel" : "x y",
   "content" : MyPermClass().get(request)}

For ``rel``, replace x and y with the the *Add form* size (the
one that appears when you click on the ``Add permission`` button.

For ``content``, replace *MyPermClass* with the appropriate name.

.. _permsgetclass:

PermsGetClass
^^^^^^^^^^^^^

Raised to retrieve the class (inheriting from ``Permissions``)
implementing a specific role. This event is used to add or delete or
new instance of this role. The role's name is available inside the
``role`` argument.

Callbacks listening to this event must return the class object
corresponding to the given ``role`` argument.

Parameters
----------

A plugin can declare its own parameters. There are two levels available:
 * 'Administration' parameters : used to configure the plugin, editable inside the *Admin > Settings > Parameters* page,
 * 'User' parameters : per-user parameters (or preferences), editable inside the *Options > Preferences* page.

Playing with parameters
^^^^^^^^^^^^^^^^^^^^^^^

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
------------------------

Custom permissions roles can be added to Modoboa. If you to want to
integrate the default permissions panel (*Admin > Permissions*), each
role you add must inherit from the ``Permissions`` (file
``admin/permissions.py``) class and implement all its methods.

See :ref:`permsgettables` and :ref:`permsgetclass` to learn how to
integrate your custom roles.


