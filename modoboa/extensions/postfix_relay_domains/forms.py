from django import forms
from .models import RelayDomain


class RelayDomainForm(forms.ModelForm):

    class Meta:
        model = RelayDomain
        exclude = ['dates']
        widgets = {
            'service': forms.Select(attrs={'class': 'span2'})
        }
