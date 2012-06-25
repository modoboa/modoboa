# coding: utf-8
import re
from django.utils.translation import ugettext as _
from django import forms
from django.forms.widgets import MultiWidget, TextInput
from django.forms.fields import MultiValueField
from django.core.exceptions import ValidationError
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
from django.utils.html import conditional_escape

class CreationWizard(object):
    def __init__(self, done_cb):
        self.steps = []
        self.done_cb = done_cb

    def add_step(self, cls, title, buttons, new_args=None):
        self.steps += [dict(cls=cls, title=title, buttons=buttons, new_args=new_args)]

    def create_forms(self, data=None):
        for step in self.steps:
            args = []
            if step.has_key("new_args") and step["new_args"]:
                args += step["new_args"]
            if data:
                args.append(data)
            step["form"] = step["cls"](*args)

    def validate_step(self, request):
        stepid = request.POST.get("stepid", None)
        if stepid is None:
            return -1, _("Invalid request")

        stepid = stepid.replace("step", "")
        stepid = int(stepid) - 1
        if stepid < 0 or stepid >= len(self.steps):
            return -1, _("Invalid request")
        self.create_forms(request.POST)
        if self.steps[stepid]["form"].is_valid():
            if stepid == len(self.steps) - 1:
                self.done_cb(self.steps)
                return 2, None
            return 1, stepid
        return 0, stepid

    def get_title(self, stepid):
        return "%d. %s" % (stepid + 1, self.steps[stepid]["title"])

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
            if self.fields.has_key(v[0]):
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
            if fd.has_key("new_args"):
                args += fd["new_args"]
            if data:
                args.append(data)
            if instances:
                if hasattr(self, "check_%s" % fd["id"]):
                    if not getattr(self, "check_%s" % fd["id"])(instances[fd["id"]]):
                        to_remove += [fd]
                        continue
                kwargs["instance"] = instances[fd["id"]]
            if classes and classes.has_key(fd["id"]):
                fd["instance"] = classes[fd["id"]](*args, **kwargs)
            else:
                fd["instance"] = fd["cls"](*args, **kwargs)
        map(lambda fd: self.forms.remove(fd), to_remove)
        self.active_id = self.forms[0]["id"]

    def _before_is_valid(self, form):
        return True
    
    def is_valid(self, mandatory_only=False, optional_only=False):
        to_remove = []
        for f in self.forms:
            if mandatory_only and \
               (not f.has_key("mandatory") or not f["mandatory"]):
                continue
            elif optional_only and \
               (f.has_key("mandatory") and f["mandatory"]):
                continue
            if not self._before_is_valid(f):
                to_remove.append(f)
                continue
            if not f["instance"].is_valid():
                self.active_id = f["id"]
                return False
        map(lambda fd: self.forms.remove(fd), to_remove)
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
        import re
        is_valid_host._re = re.compile(r'^([0-9a-z][-\w]*[0-9a-z]\.)+[a-z0-9\-]{2,15}$')
    return bool(is_valid_host._re.match(host))

def validate_domain_name(value):
    if not is_valid_host(value):
        raise ValidationError(_('Enter a valid domain name'), 'invalid')

class DomainNameField(forms.CharField):
    """
    A subclass of CharField that only accepts a valid domain name.
    """
    default_error_messages = {
        'invalid' : _('Enter a valid domain name')
        }

    default_validators = [validate_domain_name]

    def clean(self, value):
        value = self.to_python(value).strip()
        return super(DomainNameField, self).clean(value)
