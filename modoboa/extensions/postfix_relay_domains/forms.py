from django import forms
from django.http import QueryDict
from django.utils.translation import ugettext as _, ugettext_lazy
from modoboa.lib import events
from modoboa.lib.formutils import DynamicForm, DomainNameField
from modoboa.extensions.admin.models import Domain, DomainAlias
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
        """Custom fields validaton.

        We want to prevent duplicate names between domains, relay
        domains, domain aliases and relay domain aliases.

        The validation way is not very smart...
        """
        super(RelayDomainForm, self).clean()
        if self._errors:
            raise forms.ValidationError(self._errors)
        cleaned_data = self.cleaned_data
        for dtype, label in [(Domain, _('domain')),
                             (DomainAlias, _('domain alias')),
                             (RelayDomainAlias, _('relay domain alias'))]:
            try:
                dtype.objects.get(name=cleaned_data['name'])
            except dtype.DoesNotExist:
                pass
            else:
                self._errors["name"] = self.error_class(
                    [_("A %s with this name already exists" % label)]
                )
                del cleaned_data["name"]
                break

        for k in cleaned_data.keys():
            if not k.startswith("aliases"):
                continue
            if not cleaned_data[k]:
                del cleaned_data[k]
                continue
            for dtype, name in [(RelayDomain, _('relay domain')),
                                (DomainAlias, _('domain alias')),
                                (Domain, _('domain'))]:
                try:
                    dtype.objects.get(name=cleaned_data[k])
                except dtype.DoesNotExist:
                    pass
                else:
                    self._errors[k] = self.error_class(
                        [_("A %s with this name already exists" % name)]
                    )
                    del cleaned_data[k]
                    break

        return cleaned_data

    def save(self, user, commit=True):
        """Custom save method.

        As relay domain aliases are defined using the same form as
        relay domains, we need to save them manually.

        :param ``User`` user: connected user
        """
        rd = super(RelayDomainForm, self).save(commit=False)
        if commit:
            rd.save()
            aliases = []
            for k, v in self.cleaned_data.iteritems():
                if not k.startswith("aliases"):
                    continue
                if v in ["", None]:
                    continue
                aliases.append(v)
            for rdalias in rd.relaydomainalias_set.all():
                if not rdalias.name in aliases:
                    rdalias.delete()
                else:
                    aliases.remove(rdalias.name)
            if aliases:
                events.raiseEvent(
                    "CanCreate", user, "relay_domain_aliases", len(aliases)
                )
                for alias in aliases:
                    try:
                        rd.relaydomainalias_set.get(name=alias)
                    except RelayDomainAlias.DoesNotExist:
                        pass
                    else:
                        continue
                    al = RelayDomainAlias(
                        name=alias, target=rd, enabled=rd.enabled
                    )
                    al.save(creator=user)
        return rd
