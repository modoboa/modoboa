"""Form management utilities."""

import abc
import re
from collections import OrderedDict

from django.forms import TypedChoiceField
from django.forms.fields import Field
from django.forms.widgets import RadioSelect
from django.shortcuts import render
from django.utils.encoding import force_str
from django.utils.translation import ugettext as _, ugettext_lazy

from modoboa.lib.exceptions import BadRequest
from modoboa.lib.web_utils import render_to_json_response

ABC = abc.ABCMeta(force_str("ABC"), (object,), {})


class WizardStep(object):
    """A wizard step."""

    def __init__(self, uid, formclass, title, formtpl=None, new_args=None):
        """Constructor."""
        self.uid = uid
        self._cls = formclass
        self.title = title
        self.formtpl = formtpl
        self._new_args = new_args
        self._prev = None
        self._next = None
        self.form = None

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

    def check_access(self, wizard):
        """Check if this step should be displayed or not."""
        return True

    def create_form(self, data=None):
        """Instantiate a new form."""
        args = []
        if self._new_args is not None:
            args += self._new_args
        if data:
            args.append(data)
        self.form = self._cls(*args)


class WizardForm(ABC):
    """Custom wizard."""

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
            for name, value in list(step.form.errors.items()):
                if name == "__all__":
                    continue
                result[name] = value
        return result

    @property
    def first_step(self):
        """Return the first step."""
        return self.steps[0] if self.steps else None

    def add_step(self, step):
        """Add a new step to the wizard."""
        if self.steps:
            step.prev = self.steps[-1]
            self.steps[-1].next = step
        self.steps += [step]

    def create_forms(self, data=None):
        for step in self.steps:
            step.create_form(data)

    def _get_step_id(self):
        """Retrieve the step identifier from the request."""
        stepid = self.request.POST.get("stepid", None)
        if stepid is None:
            raise BadRequest(_("Invalid request"))
        stepid = int(stepid.replace("step", ""))
        if stepid < 0:
            raise BadRequest(_("Invalid request"))
        return min(stepid, len(self.steps))

    def previous_step(self):
        """Go back to the previous step."""
        stepid = self._get_step_id()
        stepid -= 2
        self.create_forms(self.request.POST)
        for step in self.steps:
            step.form.is_valid()
        while stepid >= 0:
            if self.steps[stepid].check_access(self):
                break
            stepid -= 1
        return render_to_json_response({
            "title": self.steps[stepid].title, "id": self.steps[stepid].uid,
            "stepid": stepid
        })

    def next_step(self):
        """Go to the next step if previous forms are valid."""
        stepid = self._get_step_id()
        self.create_forms(self.request.POST)
        statuses = []
        for cpt in range(0, stepid):
            if self.steps[cpt].check_access(self):
                statuses.append(self.steps[cpt].form.is_valid())
        if False in statuses:
            return render_to_json_response({
                "stepid": stepid, "id": self.steps[stepid - 1].uid,
                "form_errors": self.errors
            }, status=400)
        while stepid < len(self.steps):
            if self.steps[stepid].check_access(self):
                break
            stepid += 1
        if stepid == len(self.steps):
            return self.done()
        return render_to_json_response({
            "title": self.steps[stepid].title, "id": self.steps[stepid].uid,
            "stepid": stepid
        })

    def extra_context(self, context):
        """Provide additional information to template's context.
        """
        pass

    def process(self):
        """Process the request."""
        if self.request.method == "POST":
            if self.request.POST.get("target", "next") == "next":
                return self.next_step()
            return self.previous_step()
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

    """
    A form which accepts dynamic fields.

    We consider a field to be dynamic when it can appear multiple
    times within the same request.

    """

    fields = {}
    data = {}

    def _create_field(self, typ, name, value=None, pos=None):
        """Create a new form field.
        """
        self.fields[name] = typ(label="", required=False)
        if value is not None:
            self.fields[name].initial = value
        if pos:
            order = list(self.fields.keys())
            order.remove(name)
            order.insert(pos, name)
            self.fields = OrderedDict((key, self.fields[key]) for key in order)

    def _load_from_qdict(self, qdict, pattern, typ):
        """Load all instances of a field from a ``QueryDict`` object.

        :param ``QueryDict`` qdict: a QueryDict object
        :param string pattern: pattern used to find field instances
        :param typ: a form field class
        """
        expr = re.compile(r'%s_\d+' % pattern)
        values = []
        for k, v in list(qdict.items()):
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
    Simple forms container.

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
                mname = "check_%s" % fd["id"]
                if hasattr(self, mname):
                    if not getattr(self, mname)(instances[fd["id"]]):
                        to_remove += [fd]
                        continue
                kwargs["instance"] = instances[fd["id"]]
            if classes is not None and fd["id"] in classes:
                fd["instance"] = classes[fd["id"]](*args, **kwargs)
            else:
                fd["instance"] = fd["cls"](*args, **kwargs)
        self.forms = [form for form in self.forms if form not in to_remove]
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
            for name, value in list(f["instance"].errors.items()):
                if name == "__all__":
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
               ("mandatory" not in f or not f["mandatory"]):
                continue
            elif optional_only and ("mandatory" in f and f["mandatory"]):
                continue
            if not self._before_is_valid(f):
                to_remove.append(f)
                continue
            if not f["instance"].is_valid():
                self.active_id = f["id"]
                return False
        self.forms = [f for f in self.forms if f not in to_remove]
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
                {"form_errors": self.errors}, status=400
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


class HorizontalRadioSelect(RadioSelect):
    template_name = "common/horizontal_select.html"
    option_template_name = "common/horizontal_select_option.html"


class SeparatorField(Field):
    """Custom field to represent a separator."""

    def __init__(self, *args, **kwargs):
        kwargs["required"] = False
        super(SeparatorField, self).__init__(*args, **kwargs)


class YesNoField(TypedChoiceField):
    """A yes/no form field."""

    def __init__(self, *args, **kwargs):
        """Constructor."""
        kwargs.update({
            "choices": (
                (True, ugettext_lazy("Yes")),
                (False, ugettext_lazy("No"))
            ),
            "widget": HorizontalRadioSelect(),
            "coerce": lambda x: x == "True"
        })
        super(YesNoField, self).__init__(*args, **kwargs)
