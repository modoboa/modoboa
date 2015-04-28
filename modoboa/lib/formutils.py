# coding: utf-8
import re
import abc

from django.shortcuts import render
from django.utils.translation import ugettext as _, ugettext_lazy
from django.forms import ChoiceField
from django.forms.widgets import RadioSelect, RadioInput
from django.forms.fields import CharField, Field
from django.core.exceptions import ValidationError
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
from django.utils.html import conditional_escape

from modoboa.lib.exceptions import BadRequest
from modoboa.lib.webutils import render_to_json_response


class WizardStep(object):
    """A wizard step.
    """
    def __init__(self, cls, title, formtpl=None, new_args=None):
        """Constructor.

        """
        self._cls = cls
        self._title = title
        self.formtpl = formtpl
        self._new_args = new_args
        self._prev = None
        self._next = None
        self.index = None
        self.form = None

    @property
    def title(self):
        """Return step title"""
        if self.index is None:
            return self._title
        return "%d. %s" % (self.index + 1, self._title)

    @property
    def prev(self):
        return self._prev

    @prev.setter
    def prev(self, step):
        self._prev = step

    @property
    def next(self):
        return self._next

    @next.setter
    def next(self, step):
        self._next = step

    def create_form(self, data=None):
        args = []
        if self._new_args is not None:
            args += self._new_args
        if data:
            args.append(data)
        self.form = self._cls(*args)


class WizardForm(object):
    """Custom wizard.
    """
    __metaclass__ = abc.ABCMeta

    template_name = "common/wizard_forms.html"

    def __init__(self, request, submit_button_label=None):
        self.request = request
        self.steps = []
        self._submit_button_label = submit_button_label

    @property
    def submit_button_label(self):
        if self._submit_button_label is None:
            self._submit_button_label = _("Submit")
        return self._submit_button_label

    @property
    def errors(self):
        result = {}
        for step in self.steps:
            for name, value in step.form.errors.items():
                if name == '__all__':
                    continue
                result[name] = value
        return result

    @property
    def first_step(self):
        """Return the first step.
        """
        return self.steps[0] if self.steps else None

    def add_step(self, cls, title, formtpl=None, new_args=None):
        """Add a new step to the wizard.
        """
        step = WizardStep(cls, title, formtpl, new_args)
        if self.steps:
            step.prev = self.steps[-1]
            self.steps[-1].next = step
        self.steps += [step]
        step.index = len(self.steps) - 1

    def create_forms(self, data=None):
        for step in self.steps:
            step.create_form(data)

    def validate_step(self):
        stepid = self.request.POST.get("stepid", None)
        if stepid is None:
            raise BadRequest(_("Invalid request"))
        stepid = int(stepid.replace("step", ""))
        if stepid < 0 or stepid > len(self.steps):
            raise BadRequest(_("Invalid request"))
        self.create_forms(self.request.POST)
        statuses = []
        for cpt in xrange(0, stepid):
            statuses.append(self.steps[cpt].form.is_valid())
        if False in statuses:
            return render_to_json_response({
                'stepid': stepid, 'form_errors': self.errors
            }, status=400)
        if stepid == len(self.steps):
            return self.done()
        return render_to_json_response(
            {'title': self.steps[stepid].title, 'stepid': stepid}
        )

    def extra_context(self, context):
        """Provide additional information to template's context.
        """
        pass

    def process(self):
        """Process the request.
        """
        if self.request.method == "POST":
            return self.validate_step()
        self.create_forms()
        context = {"wizard": self}
        self.extra_context(context)
        return render(self.request, self.template_name, context)

    @abc.abstractmethod
    def done(self):
        """Method to exexute when all steps are validated.

        Must be implemented by all sub classes.

        :rtype: HttpResponse
        """


class DynamicForm(object):
    """A form which accepts dynamic fields.

    We consider a field to be dynamic when it can appear multiple
    times within the same request.

    """
    def _create_field(self, typ, name, value=None, pos=None):
        """Create a new form field.
        """
        self.fields[name] = typ(label="", required=False)
        if value is not None:
            self.fields[name].initial = value
        if pos:
            self.fields.keyOrder.remove(name)
            self.fields.keyOrder.insert(pos, name)

    def _load_from_qdict(self, qdict, pattern, typ):
        """Load all instances of a field from a ``QueryDict`` object.

        :param ``QueryDict`` qdict: a QueryDict object
        :param string pattern: pattern used to find field instances
        :param typ: a form field class
        """
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

    template_name = "common/tabforms.html"

    def __init__(self, request, instances=None, classes=None):
        self.request = request
        self.instances = {}
        to_remove = []
        for fd in self.forms:
            args = []
            kwargs = {}
            if "new_args" in fd:
                args += fd["new_args"]
            if request.method == "POST":
                args.append(request.POST)
            if instances is not None:
                self.instances = instances
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
        """Return validation errors.

        We aggregate all form errors into one dictionary.

        :rtype: dict
        """
        result = {}
        for f in self.forms:
            for name, value in f['instance'].errors.items():
                if name == '__all__':
                    continue
                result[name] = value
        return result

    def is_valid(self, mandatory_only=False, optional_only=False):
        """Check if the form is valid.

        :param boolean mandatory_only:
        :param boolean optional_only:
        """
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

    @abc.abstractmethod
    def save(self):
        """Save objects here.
        """

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

    def extra_context(self, context):
        """"Provide additional information to template's context.
        """
        pass

    @abc.abstractmethod
    def done(self):
        """Actions to execute after the form has been validated and saved.

        :rtype: HttpResponse instance
        """

    def process(self):
        """Process the received request.
        """
        if self.request.method == "POST":
            if self.is_valid():
                self.save()
                return self.done()
            return render_to_json_response(
                {'form_errors': self.errors}, status=400
            )
        context = {
            "tabs": self,
        }
        if self.forms:
            context.update({
                "action_label": _("Update"),
                "action_classes": "submit",
            })
        self.extra_context(context)
        active_tab_id = self.request.GET.get("active_tab", "default")
        if active_tab_id != "default":
            context["tabs"].active_id = active_tab_id
        return render(self.request, self.template_name, context)

#
# Custom fields from here
#


def is_valid_hostname(hostname):
    """Domain name validaton."""
    if len(hostname) > 255:
        return False
    if hostname[-1] == ".":
        hostname = hostname[:-1]  # strip exactly one dot from the
                                  # right, if present
    allowed = re.compile(r"(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
    return all(allowed.match(x) for x in hostname.split("."))


def validate_domain_name(value):
    if not is_valid_hostname(value):
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
