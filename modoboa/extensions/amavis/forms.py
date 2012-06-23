# coding: utf-8

from django import forms
from models import Policy, Users
from modoboa.lib.formutils import InlineRadioSelect

class DomainPolicyForm(forms.ModelForm):
    class Meta:
        model = Policy
        fields = ('bypass_virus_checks', 'bypass_spam_checks', 
                  'spam_tag2_level', 'spam_modifies_subj',
                  'spam_kill_level', 'bypass_banned_checks')
        widgets = {
            'bypass_spam_checks' : InlineRadioSelect(),
            'bypass_virus_checks' : InlineRadioSelect(),
            'bypass_banned_checks' : InlineRadioSelect(),
            'spam_modifies_subj' : InlineRadioSelect(attrs={'class' : 'span1'}),
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
