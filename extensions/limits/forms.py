# coding: utf-8

from django import forms
from django.utils.translation import ugettext_noop as _
from django.contrib.auth.models import User, Group
from models import *

class ResellerForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("username", "first_name", "last_name", "email")

    def save(self, commit=True):
        user = super(ResellerForm, self).save(commit=False)
        if self.cleaned_data.has_key("password1"):
            user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
            grp = Group.objects.get(name="Resellers")
            if not grp in user.groups.all():
                user.groups.add(grp)
                user.save()
            try:
                pool = LimitsPool.objects.get(user=user)
            except LimitsPool.DoesNotExist:
                pool = LimitsPool()
                pool.user = user
                pool.save()
        return user

class ResellerWithPasswordForm(ResellerForm):
    password1 = forms.CharField(label=_("Password"), widget=forms.PasswordInput)
    password2 = forms.CharField(label=_("Confirmation"), 
                                widget=forms.PasswordInput,
        help_text = _("Enter the same password as above, for verification."))

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1", "")
        password2 = self.cleaned_data["password2"]
        if password1 != password2:
            raise forms.ValidationError(_("The two password fields didn't match."))
        return password2

class LimitsPoolForm(forms.ModelForm):
    class Meta:
        model = LimitsPool
        fields = ("maxdomains", "maxdomaliases", "maxmboxes", "maxmbaliases")
        


