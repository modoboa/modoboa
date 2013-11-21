#######
Modoboa
#######

|travis| |latest-version| |downloads|

Modoboa is a mail hosting and management platform including a modern
and simplified Web User Interface. It provides useful components such
as an administration panel or a webmail.

Modoboa integrates with well known software such as `Postfix
<http://postfix.org/>`_ or `Dovecot <http://dovecot.org/>`_. A SQL
database (`MySQL <http://www.mysql.com>`_, `PostgreSQL
<http://www.postgresql.org/>`_ or `SQLite <http://www.sqlite.org>`_)
is used as a central point of communication between all components.

Modoboa is developed with modularity in mind, expanding it is really
easy. Actually, all current features are extensions.

It is written in Python and uses the `Django
<https://www.djangoproject.com>`_, `jQuery <http://jquery.com>`_ and
`Bootstap, from Twitter <http://twitter.github.com/bootstrap/>`_
frameworks.

*************
Main features
*************

* Administration panel
* `Amavisd-new <http://www.amavis.org>`_ frontend
* Webmail
* Per-user Sieve filters
* Autoreply messages for Postfix
* Graphical statistics about email traffic

*************
Documentation
*************

A detailled `documentation <https://modoboa.readthedocs.org/>`_ will help you
to install, use or extend Modoboa.

******
Issues
******

Modoboa is currently using redmine for project management and issues
tracking. Report issues and/or ask for enhancements on
`dev.modoboa.org <http://dev.modoboa.org/>`_.

*************
External code
*************

The following external libraries are provided with Modoboa:

* `jQuery version 1.9.1 <http://www.jquery.org/>`_
* `jQuery-UI 1.10+ <http://jqueryui.com/>`_
* `Bootstrap, from Twitter version 2.3.2 <http://twitter.github.com/bootstrap/>`_
* `Bootstrap datetimepicker <http://www.malot.fr/bootstrap-datetimepicker/index.php>`_

.. |latest-version| image:: https://pypip.in/v/modoboa/badge.png
   :alt: Latest version on Pypi
   :target: https://crate.io/packages/modoboa/
.. |downloads| image:: https://pypip.in/d/modoboa/badge.png
   :alt: Downloads from Pypi
   :target: https://crate.io/packages/modoboa/
.. |travis| image:: https://travis-ci.org/tonioo/modoboa.png?branch=master
   :target: https://travis-ci.org/tonioo/modoboa

.. image:: https://d2weczhvl823v0.cloudfront.net/tonioo/modoboa/trend.png
   :alt: Bitdeli badge
   :target: https://bitdeli.com/free
