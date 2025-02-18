"""Custom forms."""

from collections import OrderedDict

from django import forms
from django.utils import timezone
from django.utils.translation import gettext as _, gettext_lazy

from modoboa.lib import form_utils
from modoboa.parameters import forms as param_forms, tools as param_tools
from .models import ARmessage


class ARmessageForm(forms.ModelForm):
    """Form to define an auto-reply message."""

    fromdate = forms.DateTimeField(
        label=gettext_lazy("From"),
        required=False,
        help_text=gettext_lazy(
            "Activate your auto reply from this date. " "Format : YYYY-MM-DD HH:mm:ss"
        ),
        widget=forms.TextInput(attrs={"class": "datefield form-control"}),
    )
    untildate = forms.DateTimeField(
        label=gettext_lazy("Until"),
        required=False,
        help_text=gettext_lazy(
            "Activate your auto reply until this date. " "Format : YYYY-MM-DD HH:mm:ss"
        ),
        widget=forms.TextInput(attrs={"class": "datefield form-control"}),
    )
    subject = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))
    content = forms.CharField(
        widget=forms.Textarea(attrs={"class": "form-control"}),
        help_text=gettext_lazy(
            "The content of your answer. You can use the following variables, "
            "which will be automatically replaced by the appropriate value: "
            "%(name)s, %(fromdate)s, %(untildate)s"
        ),
    )

    class Meta:
        model = ARmessage
        fields = ("subject", "content", "enabled", "fromdate", "untildate")

    def __init__(self, *args, **kwargs):
        self.mailbox = args[0]
        super().__init__(*args[1:], **kwargs)
        self.fields = OrderedDict(
            (key, self.fields[key])
            for key in ["subject", "content", "fromdate", "untildate", "enabled"]
        )
        if not self.instance.pk:
            self.fields["subject"].initial = param_tools.get_global_parameter(
                "default_subject"
            )
            self.fields["content"].initial = param_tools.get_global_parameter(
                "default_content"
            ) % {"name": self.mailbox.user.fullname}
        instance = kwargs.get("instance")
        if instance is not None:
            if instance.enabled:
                self.fields["fromdate"].initial = instance.fromdate.replace(
                    second=0, microsecond=0
                )
                self.fields["untildate"].initial = kwargs["instance"].untildate
            else:
                self.fields["fromdate"].initial = None

    def clean(self):
        """Custom fields validaton.

        We want to be sure that fromdate < untildate and that they are
        both in the future ONLY IF the autoreply is beeing activated.

        """
        cleaned_data = super().clean()
        if not cleaned_data.get("fromdate"):
            cleaned_data["fromdate"] = timezone.now()
        if not cleaned_data["enabled"]:
            return cleaned_data
        untildate = cleaned_data.get("untildate")
        if untildate is not None:
            if untildate < timezone.now():
                self.add_error("untildate", _("This date is over"))
            elif untildate < cleaned_data["fromdate"]:
                self.add_error("untildate", _("Must be greater than start date"))
        return cleaned_data

    def save(self, commit=True):
        """Custom save method."""
        instance = super().save(commit=False)
        instance.mbox = self.mailbox
        if commit:
            instance.save()
        return instance


class ParametersForm(param_forms.AdminParametersForm):
    """General parameters."""

    app = "postfix_autoreply"

    general_sep = form_utils.SeparatorField(label=gettext_lazy("General"))

    autoreplies_timeout = forms.IntegerField(
        label=gettext_lazy("Automatic reply timeout"),
        initial=86400,
        help_text=gettext_lazy(
            "Timeout in seconds between two auto-replies to the same recipient"
        ),
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    default_subject = forms.CharField(
        label=gettext_lazy("Default subject"),
        initial=gettext_lazy("I'm off"),
        help_text=gettext_lazy(
            "Default subject used when an auto-reply message is created "
            "automatically"
        ),
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    default_content = forms.CharField(
        label=gettext_lazy("Default content"),
        initial=gettext_lazy(
            """I'm currently off. I'll answer as soon as I come back.

Best regards,
%(name)s
"""
        ),
        help_text=gettext_lazy(
            "Default content used when an auto-reply message is created "
            "automatically. The '%(name)s' macro will be replaced by the "
            "user's full name."
        ),
        widget=forms.widgets.Textarea(attrs={"class": "form-control"}),
    )

    def clean_default_content(self):
        """Check if the provided value is valid.

        Must be a valid format string which will be used with the %
        operator.
        """
        tpl = self.cleaned_data["default_content"]
        try:
            tpl % {"name": "Antoine Nguyen"}
        except (KeyError, ValueError):
            raise forms.ValidationError(gettext_lazy("Invalid syntax")) from None
        return tpl


def load_settings():
    """Load app settings."""
    from modoboa.parameters import tools as param_tools

    param_tools.registry.add("global", ParametersForm, _("Automatic replies"))
