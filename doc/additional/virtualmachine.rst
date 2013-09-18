Using the virtual machine
*************************

Introduction
============

A virtual machine with a ready-to-use Modoboa setup is available `here
<http://modoboa.org/resources/modoboa.vmdk.bz2>`_. It is composed of
the following components:

* Debian 6.0 (squeeze)
* Modoboa and its prerequisites
* MySQL
* Postfix
* Dovecot
* nginx and gunicorn

Actually, it is the result you obtain if you follow the official
documentation.

The disk image is using the `VMDK
<http://en.wikipedia.org/wiki/VMDK>`_ format and is compressed using
bzip2. To decompress it, just run the following command::

  $ bunzip2 modoboa.vmdk.bz2

If you can't use the vmdk format, you can use `qemu
<http://qemu.org/>`_ to convert it to another one. For example::

  $ qemu-img convert modoboa.vmdk -O qcow2 modoboa.qcow2

Then, just use your prefered virtualization software (qemu, kvm,
virtualbox, etc.) to start the machine. You'll need to configure at
least one bridged network interface if you want to be able to play
with Modoboa, ie. your machine must be visible from your network.

The default network interface of the machine (``eth0``) is configured
to use the DHCP protocol.

Connect to the machine
======================

The following UNIX users are available if you want to connect to the system:

===== ======== ====================
Login Password Description
===== ======== ====================
root  demo     the root user
demo  demo     an unpriviliged user
===== ======== ====================

To connect to Modoboa, first connect to the system and retrieve its
current network address like this::

  $ /sbin/ifconfig eth0

Once you know its address, open a web browser and go to this url::

  http://<ip_address>/admin/

You should see the login page. Here are the users available by default:

================ ======== ============================================
Login            Password Capabitilies
================ ======== ============================================
admin            password Default super administrator. Can do anything 
                          on the admin but can't access applications

admin@demo.local admin    Administrator of the domain *demo.local*.
                          Can administrater its domain and access to 
                          applications.

user@demo.local  user     Simple user. Can access to applications.
================ ======== ============================================
