# coding: utf-8
from django.utils.translation import ugettext_lazy
from modoboa.lib import parameters

parameters.register_user("LANG", type="list", deflt="en",
                         label=ugettext_lazy("Prefered language"),
                         values=[("de", "deutsch"), ("en", "english"),
                                 ("es", "español"), ("fr", "français"),
                                 ("pt", "português")],
                         help=ugettext_lazy("Prefered language to display pages"),
                         app="general")
