"""
Postfix relay domains extension forms.
"""
from django import forms
from django.http import QueryDict
from django.utils.translation import ugettext as _, ugettext_lazy
from django.core.urlresolvers import reverse
from modoboa.lib import events
from modoboa.lib.formutils import DynamicForm, DomainNameField, TabForms
from modoboa.lib.webutils import render_to_json_response
from modoboa.extensions.admin.models import Domain, DomainAlias
from .models import RelayDomain, RelayDomainAlias


class RelayDomainFormGeneral(forms.ModelForm, DynamicForm):
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
            "service": forms.Select(attrs={"class": "form-control"})
        }

    def __init__(self, *args, **kwargs):
        self.oldname = None
        if "instance" in kwargs:
            self.oldname = kwargs["instance"].name
        super(RelayDomainFormGeneral, self).__init__(*args, **kwargs)
        self.field_widths = {
            "service": 3
        }
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
        super(RelayDomainFormGeneral, self).clean()
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

    def save(self, user, commit=True, rdomalias_post_create=False):
        """Custom save method.

        As relay domain aliases are defined using the same form as
        relay domains, we need to save them manually.

        :param ``User`` user: connected user
        """
        rd = super(RelayDomainFormGeneral, self).save(commit=False)
        if commit:
            rd.oldname = self.oldname
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
                    al.save(creator=user) \
                        if rdomalias_post_create else al.save()
        return rd


class RelayDomainForm(TabForms):
    """Specific edition form for relay domains.

    We use a *tabs* compatible form because extensions can add their
    own tab. (ex: amavis)
    """
    def __init__(self, request, *args, **kwargs):
        self.user = request.user
        self.forms = []
        if self.user.has_perm("postfix_relay_domains.change_relaydomain"):
            self.forms.append({
                'id': 'general', 'title': _("General"),
                'formtpl': 'postfix_relay_domains/relaydomain_form.html',
                'cls': RelayDomainFormGeneral, 'mandatory': True
            })

        cbargs = [self.user]
        if "instances" in kwargs:
            cbargs += [kwargs["instances"]["general"]]
        self.forms += events.raiseQueryEvent("ExtraRelayDomainForm", *cbargs)
        super(RelayDomainForm, self).__init__(request, *args, **kwargs)

    def extra_context(self, context):
        """Additional content.
        """
        rdom = self.instances["general"]
        context.update({
            'action': reverse(
                "postfix_relay_domains:relaydomain_change", args=[rdom.id]),
            'formid': 'rdomform',
            'title': rdom.name
        })

    def save(self):
        """Custom save method

        As forms interact with each other, it is easier to make custom
        code to save them.
        """
        self.forms[0]['instance'].save(
            self.request.user, rdomalias_post_create=True
        )
        for f in self.forms[1:]:
            f["instance"].save(self.request.user)

    def done(self):
        events.raiseEvent('RelayDomainModified', self.instances["general"])
        return render_to_json_response(_('Relay domain modified'))
