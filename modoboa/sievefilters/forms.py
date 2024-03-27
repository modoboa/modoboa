"""Custom forms."""

from sievelib import commands
from sievelib.managesieve import SUPPORTED_AUTH_MECHS

from django import forms
from django.http import QueryDict
from django.utils.encoding import smart_str
from django.utils.translation import gettext as _, gettext_lazy

from modoboa.admin.templatetags.admin_tags import gender
from modoboa.lib import form_utils
from modoboa.parameters import forms as param_forms

from . import constants
from . import imaputils
from . import lib


class FiltersSetForm(forms.Form):
    name = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control"}))
    active = forms.BooleanField(
        label=gender("Active", "m"),
        required=False,
        initial=False,
        help_text=gettext_lazy("Check to activate this filters set"),
    )


class FilterForm(forms.Form):
    """A dynamic form to edit a filter."""

    def __init__(self, conditions, actions, request, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.field_widths = {"match_type": 8}

        self.fields["name"] = forms.CharField(label=_("Name"))
        self.fields["match_type"] = forms.ChoiceField(
            label=_("Match type"),
            choices=[
                ("allof", _("All of the following")),
                ("anyof", _("Any of the following")),
                ("all", _("All messages")),
            ],
            initial="anyof",
            widget=form_utils.HorizontalRadioSelect(),
        )

        self.conds_cnt = 0
        for c in conditions:
            getattr(self, "_build_%s_field" % c[0])(c[1], c[2])
        self.actions_cnt = 0
        for a in actions:
            getattr(self, "_build_%s_field" % a[0])(request, *a[1:])

    def clean_name(self):
        """Check that name does not contain strange chars."""
        if "#" in self.cleaned_data["name"]:
            raise forms.ValidationError(_("Wrong filter name"))
        return self.cleaned_data["name"]

    def _build_header_field(self, name, op, value):
        """Add a new header field to form."""
        targets = []
        ops = []
        vfield = None
        for tpl in constants.CONDITION_TEMPLATES:
            targets += [
                (tpl["name"], tpl["label"]),
            ]
            if tpl["name"] != name:
                continue
            for opdef in tpl["operators"]:
                ops += [opdef[:2]]
                if op != opdef[0]:
                    continue
                if opdef[2] in ["string", "number"]:
                    vfield = forms.CharField(max_length=255, initial=value)

        self.fields["cond_target_%d" % self.conds_cnt] = forms.ChoiceField(
            initial=name, choices=targets
        )
        self.fields["cond_operator_%d" % self.conds_cnt] = forms.ChoiceField(
            initial=op, choices=ops
        )
        self.fields["cond_value_%d" % self.conds_cnt] = vfield
        self.conds_cnt += 1

    def _build_Subject_field(self, op, value):
        self._build_header_field("Subject", op, value)

    def _build_To_field(self, op, value):
        self._build_header_field("To", op, value)

    def _build_From_field(self, op, value):
        self._build_header_field("From", op, value)

    def _build_Cc_field(self, op, value):
        self._build_header_field("Cc", op, value)

    def _build_size_field(self, op, value):
        self._build_header_field("size", op, value)

    def _build_action_field(self, request, name, *values):
        """Add a new action field to form."""
        actions = []
        args = None
        for tpl in constants.ACTION_TEMPLATES:
            actions += [
                (tpl["name"], tpl["label"]),
            ]
            if name == tpl["name"]:
                args = tpl.get("args", [])
        self.fields["action_name_%d" % self.actions_cnt] = forms.ChoiceField(
            initial=name, choices=actions
        )
        for cnt in range(len(args)):
            arg = args[cnt]
            value = values[cnt] if len(values) > cnt else None
            aname = "action_arg_%d_%d" % (self.actions_cnt, cnt)
            if arg["type"] == "string":
                self.fields[aname] = forms.CharField(max_length=255, initial=value)
            elif arg["type"] == "boolean":
                self.fields[aname] = forms.BooleanField(
                    label=arg["label"], initial=value, required=False
                )
            elif arg["type"] == "list":
                choices = getattr(self, arg["vloader"])(request)
                self.fields[aname] = forms.ChoiceField(initial=value, choices=choices)
        self.actions_cnt += 1

    def _build_redirect_field(self, request, *values):
        self._build_action_field(request, "redirect", *values)

    def _build_reject_field(self, request, *values):
        self._build_action_field(request, "reject", *values)

    def _build_fileinto_field(self, request, *values):
        self._build_action_field(request, "fileinto", *values)

    def _build_stop_field(self, request):
        self._build_action_field(request, "stop")

    def __build_folders_list(self, folders, user, imapc, parentmb=None):
        ret = []
        for fd in folders:
            value = fd["path"] if "path" in fd else fd["name"]
            if parentmb:
                ret += [
                    (
                        value,
                        fd["name"].replace("%s%s" % (parentmb, imapc.hdelimiter), ""),
                    )
                ]
            else:
                ret += [(value, fd["name"])]
            if "sub" in fd:
                submboxes = imapc.getmboxes(user, value)
                ret += self.__build_folders_list(submboxes, user, imapc, value)
        return ret

    def userfolders(self, request):
        mbc = imaputils.get_imapconnector(request)
        ret = mbc.getmboxes(request.user)

        folders = self.__build_folders_list(ret, request.user, mbc)
        return folders

    def tofilter(self):
        """Convert form values to filter values."""
        conditions = []
        actions = []
        for cpt in range(self.conds_cnt):
            conditions += [
                (
                    self.cleaned_data["cond_target_%d" % cpt],
                    ":" + self.cleaned_data["cond_operator_%d" % cpt],
                    self.cleaned_data["cond_value_%d" % cpt],
                )
            ]
        for cpt in range(self.actions_cnt):
            action = self.cleaned_data["action_name_%d" % cpt]
            tpl = lib.find_action_template(action)
            naction = [action]
            args = {}
            for pos, argtpl in enumerate(tpl.get("args", [])):
                fieldname = "action_arg_{}_{}".format(cpt, pos)
                if fieldname not in self.cleaned_data:
                    continue
                value = self.cleaned_data[fieldname]
                if argtpl["type"] == "boolean" and isinstance(value, bool):
                    if not value:
                        continue
                    value = argtpl["value"]
                args[argtpl["name"]] = value
            if "args_order" in tpl:
                # Corresponding command requires args to be in a special order
                for name in tpl["args_order"]:
                    if name in args:
                        naction.append(args[name])
            else:
                naction += [arg for arg in args.values()]
            actions += [naction]
        return (conditions, actions)


def build_filter_form_from_qdict(request):
    conditions = []
    actions = []
    qdict = QueryDict("", mutable=True)
    qdict["name"] = request.POST["name"]
    qdict["match_type"] = request.POST["match_type"]
    cpt = 0
    i = 0
    if qdict["match_type"] != "all":
        while True:
            if cpt == int(request.POST["conds"]):
                break
            if "cond_target_%d" % i in request.POST:
                qdict["cond_target_%d" % cpt] = request.POST["cond_target_%d" % i]
                qdict["cond_operator_%d" % cpt] = request.POST["cond_operator_%d" % i]
                qdict["cond_value_%d" % cpt] = request.POST["cond_value_%d" % i]
                condtarget = request.POST["cond_target_%d" % i]
                condop = request.POST["cond_operator_%d" % i]
                condvalue = request.POST["cond_value_%d" % i]
                conditions += [(condtarget, condop, condvalue)]
                cpt += 1
            i += 1
    cpt = 0
    i = 0
    while True:
        if cpt == int(request.POST["actions"]):
            break
        if "action_name_%d" % i in request.POST:
            qdict["action_name_%d" % cpt] = request.POST["action_name_%d" % i]
            action = request.POST["action_name_%d" % i]
            argcpt = 0
            args = []
            while True:
                try:
                    qdict["action_arg_%d_%d" % (cpt, argcpt)] = request.POST[
                        "action_arg_%d_%d" % (i, argcpt)
                    ]
                    args += [request.POST["action_arg_%d_%d" % (i, argcpt)]]
                except KeyError:
                    break
                argcpt += 1
            args = [action] + args
            actions += [args]
            cpt += 1
        i += 1

    return FilterForm(conditions, actions, request, qdict)


def build_filter_form_from_filter(request, name, fobj):
    match_type = fobj["test"].name
    conditions = []
    for t in fobj["test"]["tests"]:
        if isinstance(t, commands.TrueCommand):
            match_type = "all"
            conditions += [("Subject", "contains", "")]
            break
        elif isinstance(t, commands.SizeCommand):
            conditions += [("size", t["comparator"][1:], t["limit"])]
        else:
            operator_prefix = ""
            if isinstance(t, commands.NotCommand):
                t = t["test"]
                operator_prefix = "not"
            conditions += [
                (
                    smart_str(t["header-names"]).strip('"'),
                    "{}{}".format(operator_prefix, smart_str(t["match-type"])[1:]),
                    smart_str(t["key-list"]).strip('"'),
                )
            ]
    actions = []
    for c in fobj.children:
        action = (c.name,)
        tpl = lib.find_action_template(c.name)
        for argtpl in tpl.get("args", []):
            if argtpl["name"] not in c:
                continue
            value = c[argtpl["name"]]
            if argtpl["type"] == "boolean":
                value = True if value else False
            else:
                value = value.strip('"')
            action += (value,)
        actions += [action]
    form = FilterForm(conditions, actions, request)
    form.fields["name"].initial = smart_str(name)
    form.fields["match_type"].initial = match_type
    return form


def supported_auth_mechs():
    values = [("AUTO", "auto")]
    for m in SUPPORTED_AUTH_MECHS:
        values += [(m, m.lower())]
    return values


class ParametersForm(param_forms.AdminParametersForm):
    app = "sievefilters"

    sep1 = form_utils.SeparatorField(label=gettext_lazy("ManageSieve settings"))

    server = forms.CharField(
        label=gettext_lazy("Server address"),
        initial="127.0.0.1",
        help_text=gettext_lazy("Address of your MANAGESIEVE server"),
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    port = forms.IntegerField(
        label=gettext_lazy("Server port"),
        initial=4190,
        help_text=gettext_lazy("Listening port of your MANAGESIEVE server"),
        widget=forms.TextInput(attrs={"class": "form-control"}),
    )

    starttls = form_utils.YesNoField(
        label=gettext_lazy("Connect using STARTTLS"),
        initial=False,
        help_text=gettext_lazy("Use the STARTTLS extension"),
    )

    authentication_mech = forms.ChoiceField(
        label=gettext_lazy("Authentication mechanism"),
        choices=supported_auth_mechs(),
        initial="auto",
        help_text=gettext_lazy("Prefered authentication mechanism"),
        widget=forms.Select(attrs={"class": "form-control"}),
    )

    sep2 = form_utils.SeparatorField(label=gettext_lazy("IMAP settings"))

    imap_server = forms.CharField(
        label=gettext_lazy("Server address"),
        initial="127.0.0.1",
        help_text=gettext_lazy("Address of your IMAP server"),
    )

    imap_secured = form_utils.YesNoField(
        label=gettext_lazy("Use a secured connection"),
        initial=False,
        help_text=gettext_lazy("Use a secured connection to access IMAP server"),
    )

    imap_port = forms.IntegerField(
        label=gettext_lazy("Server port"),
        initial=143,
        help_text=gettext_lazy("Listening port of your IMAP server"),
    )


class UserSettings(param_forms.UserParametersForm):
    app = "sievefilters"

    sep1 = form_utils.SeparatorField(label=gettext_lazy("General"))

    editor_mode = forms.ChoiceField(
        initial="gui",
        label=gettext_lazy("Editor mode"),
        choices=[("raw", "raw"), ("gui", "simplified")],
        help_text=gettext_lazy("Select the mode you want the editor to work in"),
        widget=form_utils.HorizontalRadioSelect(),
    )

    sep2 = form_utils.SeparatorField(label=gettext_lazy("Mailboxes"))

    trash_folder = forms.CharField(
        initial="Trash",
        label=gettext_lazy("Trash folder"),
        help_text=gettext_lazy("Folder where deleted messages go"),
    )

    sent_folder = forms.CharField(
        initial="Sent",
        label=gettext_lazy("Sent folder"),
        help_text=gettext_lazy("Folder where copies of sent messages go"),
    )

    drafts_folder = forms.CharField(
        initial="Drafts",
        label=gettext_lazy("Drafts folder"),
        help_text=gettext_lazy("Folder where drafts go"),
    )

    @staticmethod
    def has_access(**kwargs):
        return hasattr(kwargs.get("user"), "mailbox")
