Contribution ares always welcome but please try to follow those few rules:

- Modoboa try to respect the `PEP8 <https://www.python.org/dev/peps/pep-0008/>`_.

- If you're adding some code, try to add some tests too. You can run the tests
  suite locally by using `tox <https://testrun.org/tox/latest/config.html>`_

There is also a few commands that can help you to contribute:

Start a basic Modoboa instance with a few fixture::

   $ tox -e serve

You can log in with admin/password.

Build the docs to see your changes::

   $ tox -e doc
   $ firefox .tox/doc/tmp/html/index.html


