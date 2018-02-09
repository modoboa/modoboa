# -*- coding: utf-8 -*-

"""A stupid extension used for tests."""

from __future__ import unicode_literals

from modoboa.core import extensions


class StupidExtension2(extensions.ModoExtension):
    """Stupid extension to use with tests."""

    name = "stupid_extension_2"
    label = "Stupid extension"
    version = "1.0.0"
    description = "A stupid extension"


extensions.exts_pool.register_extension(StupidExtension2, show=False)
