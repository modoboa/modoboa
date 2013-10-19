from django import forms
from django.http import QueryDict
from django.utils.translation import ugettext_lazy
from modoboa.lib.formutils import DynamicForm, DomainNameField
from modoboa.extensions.admin.models import Domain
from .models import RelayDomain, RelayDomainAlias


class RelayDomainForm(forms.ModelForm, DynamicForm):
    aliases = DomainNameField(
        label=ugettext_lazy("Alias(es)"),
        required=False,
        help_text=ugettext_lazy(
            "Alias(es) of this relay domain. Indicate only one name per input"
            ", press ENTER to add a new input."
        )
    )

    class Meta:
        model = RelayDomain
        exclude = ['dates']
        widgets = {
            'service': forms.Select(attrs={'class': 'span2'})
        }

    def __init__(self, *args, **kwargs):
        super(RelayDomainForm, self).__init__(*args, **kwargs)
        if args and isinstance(args[0], QueryDict):
            self._load_from_qdict(args[0], "aliases", DomainNameField)
        elif 'instance' in kwargs:
            rd = kwargs['instance']
            for pos, rdalias in enumerate(rd.relaydomainalias_set.all()):
                name = "aliases_%d" % (pos + 1)
                self._create_field(forms.CharField, name, rdalias.name, 3)

    def clean(self):
        super(RelayDomainForm, self).clean()
        if self._errors:
            raise forms.ValidationError(self._errors)
        cleaned_data = self.cleaned_data
        # try:
        #     DomainAlias.objects.get(name=name)
        # except DomainAlias.DoesNotExist:
        #     pass
        # else:
        #     self._errors["name"] = self.error_class([_("An alias with this name already exists")])
        #     del cleaned_data["name"]

        for k in cleaned_data.keys():
            if not k.startswith("aliases"):
                continue
            if cleaned_data[k] == "":
                del cleaned_data[k]
                continue
            try:
                Domain.objects.get(name=cleaned_data[k])
            except Domain.DoesNotExist:
                pass
            else:
                self._errors[k] = self.error_class([_("A domain with this name already exists")])
                del cleaned_data[k]

        return cleaned_data

    def save(self, user, commit=True):
        """Custom save method

        """
        rd = super(RelayDomainForm, self).save(commit=False)
        if commit:
            rd.save()
            for k, v in self.cleaned_data.iteritems():
                if not k.startswith("aliases"):
                    continue
                if v in ["", None]:
                    continue
                try:
                    rd.relaydomainalias_set.get(name=v)
                except RelayDomainAlias.DoesNotExist:
                    pass
                else:
                    continue
                #events.raiseEvent("CanCreate", user, "domain_aliases")
                al = RelayDomainAlias(name=v, target=rd, enabled=rd.enabled)
                al.save(creator=user)

            for rdalias in rd.relaydomainalias_set.all():
                if not filter(lambda name: self.cleaned_data[name] == rdalias.name,
                              self.cleaned_data.keys()):
                    rdalias.delete()
        return rd
