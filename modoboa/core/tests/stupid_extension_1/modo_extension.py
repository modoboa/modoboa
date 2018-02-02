# -*- coding: utf-8 -*-

"""A stupid extension used for tests."""

from __future__ import unicode_literals

from modoboa.core import extensions


class StupidExtension1(extensions.ModoExtension):
    """Stupid extension to use with tests."""

    name = "stupid_extension_1"
    label = "Stupid extension"
    version = "1.0.0"
    description = "A stupid extension"

    def load(self):
        pass

    def load_initial_data(self):
        raise RuntimeError


extensions.exts_pool.register_extension(StupidExtension1)
