############################################
Modoboa (`website <https://modoboa.org/>`_)
############################################

|workflow| |codecov| |latest-version|

`Modoboa <https://modoboa.org>`_ is a mail hosting and management platform including a modern
and simplified Web User Interface. It provides useful components such
as an administration panel and webmail.

Modoboa integrates with well known software such as `Postfix
<http://postfix.org/>`_ or `Dovecot <http://dovecot.org/>`_. A SQL
database (`MySQL <http://www.mysql.com>`_, `PostgreSQL
<http://www.postgresql.org/>`_ or `SQLite <http://www.sqlite.org>`_)
is used as a central point of communication between all components.

Modoboa is developed with modularity in mind, expanding it is really
easy. Actually, all current features are extensions.

It is written in Python 3 and uses the `Django
<https://www.djangoproject.com>`_, `jQuery <http://jquery.com>`_ and
`Bootstrap <http://getbootstrap.com/>`_
frameworks.

*************
Main features
*************

* Administration panel
* Reputation protection: `DNSBL <https://en.wikipedia.org/wiki/DNSBL>`_ checks, `DMARC <https://dmarc.org/>`_ `reports <https://github.com/modoboa/modoboa-dmarc>`_ and more
* `Amavis <http://www.amavis.org>`_ `frontend <https://github.com/modoboa/modoboa-amavis>`_
* `Webmail <https://github.com/modoboa/modoboa-webmail>`_
* `Calendar <https://github.com/modoboa/modoboa-radicale>`_
* `Address book <https://github.com/modoboa/modoboa-contacts>`_
* Per-user Sieve filters
* Autoreply messages for Postfix
* Graphical statistics about email traffic

************
Installation
************

The easiest way to install modoboa is to use the
`official installer <https://github.com/modoboa/modoboa-installer>`_.
More information is available in the documentation.

*************
Documentation
*************

A detailed `documentation <https://modoboa.readthedocs.io/>`_ will help you
to install, use or extend Modoboa.

*****************
Demo Installation
*****************

If you want to try out Modoboa, check out our `demo installation <https://demo.modoboa.org/>`_.

************
Getting help
************

Modoboa is a free software and is totally open source BUT you can hire the team if you need professional services. More information here: https://modoboa.org/en/professional-services/.

Contracting a support plan if a good way to ensure your installation stays available and up-to-date and it will help the project to be sustainable :)

*********
Community
*********

If you have any questions, you can get help through the following platforms:

* `Discord <https://discord.gg/WuQ3v3PXGR>`_
* Github: open an issue if you found a bug

*************
External code
*************

The following external libraries are provided with Modoboa:

* `jQuery version 1.9.1 <http://www.jquery.org/>`_
* `jQuery-UI 1.10+ <http://jqueryui.com/>`_
* `Bootstrap version 3.3.7 <http://getbootstrap.com/>`_
* `Bootstrap datetimepicker <http://eonasdan.github.io/bootstrap-datetimepicker/>`_

.. |latest-version| image:: https://img.shields.io/pypi/v/modoboa.svg
   :target: https://pypi.python.org/pypi/modoboa/
   :alt: Latest version on Pypi
.. |workflow| image:: https://github.com/modoboa/modoboa/actions/workflows/modoboa.yml/badge.svg
.. |codecov| image:: https://codecov.io/gh/modoboa/modoboa/graph/badge.svg?token=1E5eBxJO33
   :target: https://codecov.io/gh/modoboa/modoboa
