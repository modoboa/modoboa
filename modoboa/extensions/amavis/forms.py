# coding: utf-8

from django import forms
from models import Policy, Users
from django.utils.translation import ugettext_lazy

def is_yes(v): return v == 'Y'

class CustomInputField(forms.CharField):
    """Custom <input> field

    Most of the columns defined by amavis use the *char* type even if
    they only support 2 values (Y/N). As we want to display them using
    checkboxes, we need to make some modifications in order that
    values are correctly interpreted.
    """
    def validate(self, value):
        value = "N" if not value else "Y"
        super(CustomInputField, self).validate(value)

    def clean(self, value):
        value = "N" if not value else "Y"
        return super(CustomInputField, self).clean(value)

class DomainPolicyForm(forms.ModelForm):
    bypass_spam_checks = CustomInputField(label=ugettext_lazy("Spam filter"),
                                          widget=forms.CheckboxInput(check_test=is_yes),
                                          help_text=ugettext_lazy("enabled"))
    bypass_virus_checks = CustomInputField(label=ugettext_lazy("Virus filter"), 
                                          widget=forms.CheckboxInput(check_test=is_yes),
                                          help_text=ugettext_lazy("enabled"))
    bypass_banned_checks = CustomInputField(label=ugettext_lazy("Banned filter"), 
                                          widget=forms.CheckboxInput(check_test=is_yes),
                                          help_text=ugettext_lazy("enabled"))
    spam_modifies_subj = CustomInputField(label=ugettext_lazy("Spam marker"), 
                                          widget=forms.CheckboxInput(check_test=is_yes),
                                          help_text=ugettext_lazy("tag subject"))

    class Meta:
        model = Policy
        fields = ('bypass_virus_checks', 'bypass_spam_checks', 
                  'spam_tag2_level', 'spam_modifies_subj',
                  'spam_kill_level', 'bypass_banned_checks')
        widgets = {
            'spam_tag2_level' : forms.TextInput(attrs={'class' : 'span1'}),
            'spam_kill_level' : forms.TextInput(attrs={'class' : 'span1'}),
            }

    def __init__(self, *args, **kwargs):
        if kwargs.has_key("instance"):
            self.domain = kwargs["instance"]
            try:
                policy = Users.objects.get(email="@%s" % self.domain.name).policy
                kwargs["instance"] = policy
            except (Users.DoesNotExist, Policy.DoesNotExist), e:
                del kwargs["instance"]
        super(DomainPolicyForm, self).__init__(*args, **kwargs)

    def save(self, user, commit=True):
        p = super(DomainPolicyForm, self).save(commit=False)
        if commit:
            p.save()        
            try:
                u = Users.objects.get(policy__id=p.id)
            except Users.DoesNotExist:
                u = Users()
                u.email = "@%s" % self.domain.name
                u.fullname = self.domain.name
                u.policy = p
                u.local = "1"
                u.priority = 7
                u.save()
            p.save()
        return p
