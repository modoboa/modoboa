################################
`Modoboa <http://modoboa.org/>`_
################################

|travis| |codecov| |latest-version|

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
* `Per-user Sieve filters <https://github.com/modoboa/modoboa-sievefilters>`_
* `Autoreply messages for Postfix <https://github.com/modoboa/modoboa-postfix-autoreply>`_
* `Graphical statistics about email traffic <https://github.com/modoboa/modoboa-stats>`_

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

If you have any question, you can use the following ways to get help:

* IRC: join the ``#modoboa`` channel on Freenode
* Mailing list: join the `modoboa-users <https://groups.google.com/forum/#!forum/modoboa-users>`_ group on Google Groups
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
.. |travis| image:: https://travis-ci.org/modoboa/modoboa.png?branch=master
   :target: https://travis-ci.org/modoboa/modoboa
.. |codecov| image:: http://codecov.io/github/modoboa/modoboa/coverage.svg?branch=master
   :target: http://codecov.io/github/modoboa/modoboa?branch=master
