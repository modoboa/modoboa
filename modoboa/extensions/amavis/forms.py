# coding: utf-8
from django.utils.translation import ugettext_lazy as _
from django import forms
from models import Policy, Users


class DomainPolicyForm(forms.ModelForm):
    spam_subject_tag2_act = forms.BooleanField()

    class Meta:
        model = Policy
        fields = ('bypass_virus_checks', 'bypass_spam_checks',
                  'spam_tag2_level', 'spam_subject_tag2',
                  'spam_kill_level', 'bypass_banned_checks')
        widgets = {
            'bypass_virus_checks': InlineRadioSelect(),
            'bypass_spam_checks': InlineRadioSelect(),
            'spam_tag2_level': forms.TextInput(attrs={'class': 'span1'}),
            'spam_kill_level': forms.TextInput(attrs={'class': 'span1'}),
            'spam_subject_tag2': forms.TextInput(attrs={'class': 'span2'}),
            'bypass_banned_checks': InlineRadioSelect(),
            }

    def __init__(self, *args, **kwargs):
        if "instance" in kwargs:
            self.domain = kwargs["instance"]
            try:
                policy = Users.objects.get(email="@%s" % self.domain.name).policy
                kwargs["instance"] = policy
            except (Users.DoesNotExist, Policy.DoesNotExist), e:
                del kwargs["instance"]
        super(DomainPolicyForm, self).__init__(*args, **kwargs)
        for f in self.fields.keys():
            self.fields[f].required = False

    def save(self, user, commit=True):
        p = super(DomainPolicyForm, self).save(commit=False)
        for f in ['bypass_spam_checks', 'bypass_virus_checks', 'bypass_banned_checks']:
            if getattr(p, f) == '':
                setattr(p, f, None)

        if self.cleaned_data['spam_subject_tag2_act']:
            p.spam_subject_tag2 = None

        if commit:
            p.save()
            try:
                u = Users.objects.get(policy=p)
            except Users.DoesNotExist:
                u = Users.objects.get(email="@%s" % self.domain.name)
                u.policy = p
                p.save()
        return p
