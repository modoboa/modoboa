# coding: utf-8

from modoboa.lib import parameters
from django.utils.translation import ugettext as _

parameters.register_user("LANG", type="list", deflt="en", 
                         label=_("Prefered language"),
                         values=[("de", "deutsch"), ("en", "english"),
                                 ("es", "español"), ("fr", "français")],
                         help=_("Prefered language to display pages"),
                         app="general")
