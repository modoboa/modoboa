# coding: utf-8

from django import forms
from models import Policy, Users

class DomainPolicyForm(forms.ModelForm):

    class Meta:
        model = Policy
        fields = ('bypass_virus_checks', 'bypass_spam_checks', 'spam_modifies_subj',
                  'spam_tag2_level', 'spam_kill_level')
        widgets = {
            'bypass_spam_checks' : forms.Select(attrs={'class' : 'span1'}),
            'bypass_virus_checks' : forms.Select(attrs={'class' : 'span1'}),
            'spam_modifies_subj' : forms.Select(attrs={'class' : 'span1'}),
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

    def save(self, commit=True):
        p = super(DomainPolicyForm, self).save(commit=False)
        if commit:
            p.save()        
            print p.id
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
