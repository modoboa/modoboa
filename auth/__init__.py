# coding: utf-8
from modoboa.lib import parameters
from django.utils.translation import ugettext_lazy

parameters.register_admin("SECRET_KEY", type="string", deflt="abcdefghijklmnop",
                          help=ugettext_lazy("Key used to encrypt/decrypt passwords"))
