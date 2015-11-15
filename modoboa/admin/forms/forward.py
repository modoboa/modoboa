"""Forms related to forwards management."""

from django import forms
from django.utils.translation import ugettext as _, ugettext_lazy

from modoboa.lib.email_utils import split_mailbox
from modoboa.lib.exceptions import BadRequest, PermDeniedException

from ..models import Domain


class ForwardForm(forms.Form):
    dest = forms.CharField(
        label=ugettext_lazy("Recipient(s)"),
        widget=forms.Textarea(attrs={"class": "form-control"}),
        required=False,
        help_text=ugettext_lazy(
            "Indicate one or more recipients separated by a ','")
    )
    keepcopies = forms.BooleanField(
        label=ugettext_lazy("Keep local copies"),
        required=False,
        help_text=ugettext_lazy(
            "Forward messages and store copies into your local mailbox")
    )

    def get_recipients(self):
        recipients = []
        rawdata = self.cleaned_data["dest"].strip()
        if not rawdata:
            return recipients
        for rcpt in rawdata.split(","):
            local_part, domname = split_mailbox(rcpt)
            if not local_part or not domname:
                raise BadRequest("Invalid mailbox syntax for %s" % rcpt)
            try:
                Domain.objects.get(name=domname)
            except Domain.DoesNotExist:
                recipients += [rcpt]
            else:
                raise PermDeniedException(
                    _("You can't define a forward to a local destination. "
                      "Please ask your administrator to create an alias "
                      "instead.")
                )
        return recipients
