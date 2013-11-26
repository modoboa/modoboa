# coding: utf-8
import datetime
from django import forms
from django.utils.translation import ugettext as _, ugettext_lazy
from django.utils import timezone
from .models import ARmessage


class ARmessageForm(forms.ModelForm):
    fromdate = forms.DateTimeField(
        label=ugettext_lazy('From'),
        required=False,
        help_text=ugettext_lazy("Activate your auto reply from this date"),
        widget=forms.TextInput(
            attrs={'class': 'datefield', 'readonly': 'readonly'}
        )
    )
    untildate = forms.DateTimeField(
        label=ugettext_lazy('Until'),
        required=False,
        help_text=ugettext_lazy("Activate your auto reply until this date"),
        widget=forms.TextInput(
            attrs={'class': 'datefield', 'readonly': 'readonly'}
        )
    )

    class Meta:
        model = ARmessage
        fields = ('subject', 'content', 'enabled')

    def __init__(self, *args, **kwargs):
        super(ARmessageForm, self).__init__(*args, **kwargs)
        self.fields.keyOrder = ['subject', 'content', 'fromdate', 'untildate', 'enabled']
        if 'instance' in kwargs and kwargs['instance'] is not None:
            self.fields['fromdate'].initial = kwargs['instance'].fromdate
            self.fields['untildate'].initial = kwargs['instance'].untildate

    def clean(self):
        """Custom fields validaton.

        We want to be sure that fromdate < untildate and that they are
        both in the future.
        """
        super(ARmessageForm, self).clean()
        if self._errors:
            raise forms.ValidationError(self._errors)
        if self.cleaned_data["fromdate"] is not None:
            if self.cleaned_data["fromdate"] < timezone.now():
                self._errrors["fromdate"] = self.error_class([_("This date is over")])
                del self.cleaned_data['fromdate']
        else:
            self.cleaned_data['fromdate'] = timezone.now()
        if self.cleaned_data["untildate"] is not None:
            if self.cleaned_data["untildate"] < timezone.now():
                self._errors["untildate"] = self.error_class([_("This date is over")])
                del self.cleaned_data['untildate']
            elif self.cleaned_data['untildate'] < self.cleaned_data['fromdate']:
                self._errors["untildate"] = \
                    self.error_class([_("Must be greater than start date")])
                del self.cleaned_data['untildate']
        return self.cleaned_data
