from django import forms
from modoboa.admin.models import User, Domain, Mailbox
from django.utils.translation import ugettext as _, ugettext_lazy
from modoboa.lib.emailutils import split_mailbox
from modoboa.lib import parameters

class BadDestination(Exception):
    pass

class ProfileForm(forms.ModelForm):
    oldpassword = forms.CharField(label=ugettext_lazy("Old password"), required=False,
                                  widget=forms.PasswordInput)
    newpassword = forms.CharField(label=ugettext_lazy("New password"), required=False,
                                  widget=forms.PasswordInput)
    confirmation = forms.CharField(label=ugettext_lazy("Confirmation"), required=False,
                                   widget=forms.PasswordInput)

    class Meta:
        model = User
        fields = ("first_name", "last_name")

    def __init__(self, update_password, *args, **kwargs):
        super(ProfileForm, self).__init__(*args, **kwargs)
        if not update_password:
            del self.fields["oldpassword"]
            del self.fields["newpassword"]
            del self.fields["confirmation"]
        
    def clean_oldpassword(self):
        if self.cleaned_data["oldpassword"] == "":
            return self.cleaned_data["oldpassword"]

        if parameters.get_admin("AUTHENTICATION_TYPE", app="admin") != "local":
            return self.cleaned_data["oldpassword"]

        if not self.instance.check_password(self.cleaned_data["oldpassword"]):
            raise forms.ValidationError(_("Old password mismatchs"))
        return self.cleaned_data["oldpassword"]

    def clean_confirmation(self):
        if self.cleaned_data["newpassword"] != self.cleaned_data["confirmation"]:
            raise forms.ValidationError(_("Passwords mismatch"))
        return self.cleaned_data["confirmation"]

    def save(self, commit=True):
        user = super(ProfileForm, self).save(commit=False)
        if commit:
            if self.cleaned_data.has_key("confirmation") and \
                    self.cleaned_data["confirmation"] != "":
                user.set_password(self.cleaned_data["confirmation"], self.cleaned_data["oldpassword"])
            user.save()
        return user

class ForwardForm(forms.Form):
    dest = forms.CharField(
        label=ugettext_lazy("Recipient(s)"), 
        widget=forms.Textarea,
        required=False,
        help_text=ugettext_lazy("Indicate one or more recipients separated by a ','")
        )
    keepcopies = forms.BooleanField(
        label=ugettext_lazy("Keep local copies"), 
        required=False,
        help_text=ugettext_lazy("Forward messages and store copies into your local mailbox")
        )

    def parse_dest(self):
        self.dests = []
        rawdata = self.cleaned_data["dest"].strip()
        if rawdata == "":
            return
        for d in rawdata.split(","):
            local_part, domname = split_mailbox(d)
            if not local_part or not domname or not len(domname):
                raise BadDestination("Invalid mailbox syntax for %s" % d)
            try:
                mb = Domain.objects.get(name=domname)
            except Domain.DoesNotExist:
                self.dests += [d]
            else:
                raise BadDestination(_("You can't define a forward to a local destination. Please ask your administrator to create an alias instead."))
        
