# coding: utf-8
import re
from django.utils.translation import ugettext as _, ugettext_lazy
from django.forms import ChoiceField
from django.forms.widgets import RadioSelect, RadioInput
from django.forms.fields import CharField, Field
from django.core.exceptions import ValidationError
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
from django.utils.html import conditional_escape


class CreationWizard(object):
    def __init__(self, done_cb=None):
        self.steps = []
        self.done_cb = done_cb

    @property
    def errors(self):
        result = {}
        for step in self.steps:
            for name, value in step['form'].errors.items():
                if name == '__all__':
                    continue
                result[name] = value
        return result

    def add_step(self, cls, title, buttons, formtpl=None, new_args=None):
        self.steps += [dict(cls=cls, title=title, buttons=buttons,
                            formtpl=formtpl, new_args=new_args)]

    def create_forms(self, data=None):
        for step in self.steps:
            args = []
            if 'new_args' in step and step["new_args"]:
                args += step["new_args"]
            if data:
                args.append(data)
            step["form"] = step["cls"](*args)

    def validate_step(self, request):
        stepid = request.POST.get("stepid", None)
        if stepid is None:
            return -1, _("Invalid request")

        stepid = stepid.replace("step", "")
        stepid = int(stepid)
        if stepid < 0 or stepid > len(self.steps):
            return -1, _("Invalid request")
        self.create_forms(request.POST)
        statuses = []
        for cpt in xrange(0, stepid):
            statuses.append(self.steps[cpt]["form"].is_valid())
        if False in statuses:
            return 0, stepid
        if stepid == len(self.steps):
            if self.done_cb is not None:
                self.done_cb(self.steps)
            return 2, None
        return 1, stepid

    def get_title(self, stepid):
        return "%d. %s" % (stepid, self.steps[stepid - 1]["title"])


class DynamicForm(object):

    def _create_field(self, typ, name, value=None, pos=None):
        self.fields[name] = typ(label="", required=False)
        if value is not None:
            self.fields[name].initial = value
        if pos:
            self.fields.keyOrder.remove(name)
            self.fields.keyOrder.insert(pos, name)

    def _load_from_qdict(self, qdict, pattern, typ):
        expr = re.compile(r'%s_\d+' % pattern)
        values = []
        for k, v in qdict.iteritems():
            if k == pattern or expr.match(k):
                values.append((k, v))

        ndata = self.data.copy()
        values.reverse()
        for v in values:
            if v[0] in self.fields:
                continue
            self._create_field(typ, v[0])
            ndata[v[0]] = v[1]
        self.data = ndata


class TabForms(object):
    """
    Simple forms container

    This class tries to encapsulate multiple forms that will be
    displayed using tabs. It is different from a classical formset
    because it can contain different forms.
    """
    def __init__(self, data=None, instances=None, classes=None):
        to_remove = []
        for fd in self.forms:
            args = []
            kwargs = {}
            if "new_args" in fd:
                args += fd["new_args"]
            if data is not None:
                args.append(data)
            if instances is not None:
                if hasattr(self, "check_%s" % fd["id"]):
                    if not getattr(self, "check_%s" % fd["id"])(instances[fd["id"]]):
                        to_remove += [fd]
                        continue
                kwargs["instance"] = instances[fd["id"]]
            if classes is not None and fd["id"] in classes:
                fd["instance"] = classes[fd["id"]](*args, **kwargs)
            else:
                fd["instance"] = fd["cls"](*args, **kwargs)
        self.forms = [form for form in self.forms if not form in to_remove]
        if self.forms:
            self.active_id = self.forms[0]["id"]

    def _before_is_valid(self, form):
        return True

    @property
    def errors(self):
        result = {}
        for f in self.forms:
            for name, value in f['instance'].errors.items():
                if name == '__all__':
                    continue
                result[name] = value
        return result
    
    def is_valid(self, mandatory_only=False, optional_only=False):
        to_remove = []
        for f in self.forms:
            if mandatory_only and \
               (not 'mandatory' in f or not f["mandatory"]):
                continue
            elif optional_only and \
               ('mandatory' in f and f["mandatory"]):
                continue
            if not self._before_is_valid(f):
                to_remove.append(f)
                continue
            if not f["instance"].is_valid():
                self.active_id = f["id"]
                return False
        self.forms = [f for f in self.forms if not f in to_remove]
        return True

    def save(self, *args, **kwargs):
        raise RuntimeError

    def remove_tab(self, tabid):
        for f in self.forms:
            if f["id"] == tabid:
                self.forms.remove(f)
                break

    def __iter__(self):
        return self.forward()

    def forward(self):
        for form in self.forms:
            yield form

#
# Custom fields from here
#


def is_valid_host(host):
    """IDN compatible domain validator
    """
    host = host.encode('idna').lower()
    if not hasattr(is_valid_host, '_re'):
        is_valid_host._re = re.compile(r'^([0-9a-z][-\w]*[0-9a-z]\.)+[a-z0-9\-]{2,15}$')
    return bool(is_valid_host._re.match(host))


def validate_domain_name(value):
    if not is_valid_host(value):
        raise ValidationError(_('Enter a valid domain name'), 'invalid')


class DomainNameField(CharField):
    """
    A subclass of CharField that only accepts a valid domain name.
    """
    default_error_messages = {
        'invalid': _('Enter a valid domain name')
    }

    default_validators = [validate_domain_name]

    def clean(self, value):
        value = self.to_python(value).strip()
        return super(DomainNameField, self).clean(value)


class CustomRadioInput(RadioInput):
    def __unicode__(self):
        if 'id' in self.attrs:
            label_for = ' for="%s_%s"' % (self.attrs['id'], self.index)
        else:
            label_for = ''
        choice_label = conditional_escape(force_unicode(self.choice_label))
        return mark_safe(
            u'<label class="radio-inline" %s>%s %s</label>'
            % (label_for, self.tag(), choice_label)
        )


class InlineRadioRenderer(RadioSelect.renderer):
    def __iter__(self):
        for i, choice in enumerate(self.choices):
            yield CustomRadioInput(
                self.name, self.value, self.attrs.copy(), choice, i
            )

    def render(self):
        return mark_safe(
            u'\n'.join([u'%s\n' % force_unicode(w) for w in self])
        )


class InlineRadioSelect(RadioSelect):
    renderer = InlineRadioRenderer


class SeparatorField(Field):
    def __init__(self, *args, **kwargs):
        kwargs["required"] = False
        super(SeparatorField, self).__init__(*args, **kwargs)


class YesNoField(ChoiceField):
    def __init__(self, *args, **kwargs):
        kwargs["choices"] = [
            ("yes", ugettext_lazy("Yes")), ("no", ugettext_lazy("No"))
        ]
        kwargs["widget"] = InlineRadioSelect
        super(YesNoField, self).__init__(*args, **kwargs)
