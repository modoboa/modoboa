# coding: utf-8

"""Custom forms."""

from collections import OrderedDict

from django import forms
from django.utils import timezone
from django.utils.translation import ugettext as _, ugettext_lazy

from .models import ARmessage


class ARmessageForm(forms.ModelForm):

    fromdate = forms.DateTimeField(
        label=ugettext_lazy('From'),
        required=False,
        help_text=ugettext_lazy("Activate your auto reply from this date"),
        widget=forms.TextInput(
            attrs={'class': 'datefield form-control', 'readonly': 'readonly'}
        )
    )
    untildate = forms.DateTimeField(
        label=ugettext_lazy('Until'),
        required=False,
        help_text=ugettext_lazy("Activate your auto reply until this date"),
        widget=forms.TextInput(
            attrs={'class': 'datefield form-control', 'readonly': 'readonly'}
        )
    )
    subject = forms.CharField(
        widget=forms.TextInput(
            attrs={'class': 'form-control'}
        )
    )
    content = forms.CharField(
        widget=forms.Textarea(
            attrs={'class': 'form-control'}
        )
    )

    class Meta:
        model = ARmessage
        fields = ('subject', 'content', 'enabled')

    def __init__(self, *args, **kwargs):
        super(ARmessageForm, self).__init__(*args, **kwargs)
        self.fields = OrderedDict(
            (key, self.fields[key]) for key in
            ['subject', 'content', 'fromdate', 'untildate', 'enabled']
        )
        if 'instance' in kwargs and kwargs['instance'] is not None:
            self.fields['fromdate'].initial = \
                kwargs['instance'].fromdate.replace(second=0, microsecond=0)
            self.fields['untildate'].initial = kwargs['instance'].untildate

    def clean(self):
        """Custom fields validaton.

        We want to be sure that fromdate < untildate and that they are
        both in the future ONLY IF the autoreply is beeing activated.

        """
        super(ARmessageForm, self).clean()
        if not self.cleaned_data["enabled"]:
            return self.cleaned_data
        if self.cleaned_data["fromdate"] is not None:
            if self.cleaned_data["fromdate"] < timezone.now():
                self.add_error("fromdate", _("This date is over"))
        else:
            self.cleaned_data['fromdate'] = timezone.now()
        if self.cleaned_data["untildate"] is not None:
            untildate = self.cleaned_data["untildate"]
            if untildate < timezone.now():
                self.add_error("untildate", _("This date is over"))
            elif "fromdate" in self.cleaned_data and \
                    untildate < self.cleaned_data["fromdate"]:
                self.add_error(
                    "untildate", _("Must be greater than start date"))
        return self.cleaned_data
