# coding: utf-8
from modoboa.lib import parameters
from django.utils.translation import ugettext as _

parameters.register_admin("SECRET_KEY", type="string", deflt="abcdefghijklmnop",
                          help=_("Key used to encrypt/decrypt passwords"))
