from django import forms
from django.utils.translation import ugettext_lazy as _
from modoboa.lib.parameters import AdminParametersForm
from modoboa.lib.formutils import SeparatorField


class ParametersForm(AdminParametersForm):
    app = "limits"

    defv_sep = SeparatorField(label=_("Default limits"))
    
    deflt_domain_admins_limit = forms.IntegerField(
        label=_("Domain admins"),
        initial=0,
        help_text=_("Maximum number of allowed domain administrators for a new administrator"),
        widget=forms.widgets.TextInput(attrs={"class": "span1"})
    )
    deflt_domains_limit = forms.IntegerField(
        label=_("Domains"),
        initial=0,
        help_text=_("Maximum number of allowed domains for a new administrator"),
        widget=forms.widgets.TextInput(attrs={"class": "span1"})
    )
    deflt_domain_aliases_limit = forms.IntegerField(
        label=_("Domain aliases"),
        initial=0,
        help_text=_("Maximum number of allowed domain aliases for a new administrator"),
        widget=forms.widgets.TextInput(attrs={"class": "span1"})
    )
    deflt_mailboxes_limit = forms.IntegerField(
        label=_("Mailboxes"),
        initial=0,
        help_text=_("Maximum number of allowed mailboxes for a new administrator"),
        widget=forms.widgets.TextInput(attrs={"class": "span1"})
    )
    deflt_mailbox_aliases_limit = forms.IntegerField(
        label=_("Mailbox aliases"),
        initial=0,
        help_text=_("Maximum number of allowed aliases for a new administrator"),
        widget=forms.widgets.TextInput(attrs={"class": "span1"})
    )

    def __init__(self, *args, **kwargs):
        super(AdminParametersForm, self).__init__(*args, **kwargs)
        self._load_extra_parameters('A')
