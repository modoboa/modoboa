# coding: utf-8

from django import forms
from models import Policy, Users
from django.utils.translation import ugettext_lazy
from django.forms.widgets import RadioSelect, RadioInput
from django.utils.html import conditional_escape
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe

class CustomRadioInput(RadioInput):
    def __unicode__(self):
        if 'id' in self.attrs:
            label_for = ' for="%s_%s"' % (self.attrs['id'], self.index)
        else:
            label_for = ''
        choice_label = conditional_escape(force_unicode(self.choice_label))
        return mark_safe(u'<label class="radio inline" %s>%s %s</label>' % (label_for, self.tag(), choice_label))

class InlineRadioRenderer(RadioSelect.renderer):
    def __iter__(self):
        for i, choice in enumerate(self.choices):
            yield CustomRadioInput(self.name, self.value, self.attrs.copy(), choice, i)

    def render(self):
        return mark_safe(u'\n'.join([u'%s\n' % force_unicode(w) for w in self]))

class InlineRadioSelect(RadioSelect):
    renderer = InlineRadioRenderer

class DomainPolicyForm(forms.ModelForm):

    class Meta:
        model = Policy
        fields = ('bypass_virus_checks', 'bypass_spam_checks', 
                  'spam_tag2_level', 'spam_modifies_subj',
                  'spam_kill_level', 'bypass_banned_checks')
        widgets = {
            'bypass_virus_checks' : InlineRadioSelect(),
            'bypass_spam_checks' : InlineRadioSelect(),
            'spam_tag2_level' : forms.TextInput(attrs={'class' : 'span1'}),
            'spam_modifies_subj' : InlineRadioSelect(),
            'spam_kill_level' : forms.TextInput(attrs={'class' : 'span1'}),
            'bypass_banned_checks' : InlineRadioSelect(),
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
        for f in self.fields.keys():
            self.fields[f].required = False
    
    def save(self, user, commit=True):
        p = super(DomainPolicyForm, self).save(commit=False)
        if commit:
            p.save()
            try:
                u = Users.objects.get(policy=p)
            except Users.DoesNotExist:
                u = Users.objects.get(email="@%s" % self.domain.name)
                u.policy = p
                p.save()
        return p
