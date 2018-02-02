"""Transport forms."""

from django import forms

from . import backends, models

TYPE_TO_FIELD_MAP = {
    "int": forms.IntegerField,
    "boolean": forms.BooleanField,
    "string": forms.CharField
}


class BackendSettingsMixin(object):
    """A mixin to deal with backend settings in a model form."""

    def __init__(self, *args, **kwargs):
        """Constructor."""
        super(BackendSettingsMixin, self).__init__(*args, **kwargs)
        self.setting_field_names = []

    def inject_backend_settings(self, name, settings):
        """Inject backend settings to form."""
        for setting in settings:
            fullname = "{}_{}".format(name, setting["name"])
            options = {}
            ftype = setting.get("type", "string")
            if self.instance.pk:
                options["initial"] = self.instance._settings.get(fullname)
            elif "default" in setting:
                options["initial"] = setting["default"]
            if "widget" in setting:
                options["widget"] = setting["widget"]
            self.fields[fullname] = TYPE_TO_FIELD_MAP[ftype](
                label=setting["label"], required=False, **options)
            self.setting_field_names.append(fullname)

    def clean_backend_fields(self, name):
        """Clean backend fields."""
        self.backend = backends.manager.get_backend(name)
        for field, error in self.backend.clean_fields(self.cleaned_data):
            self.add_error(field, error)

    def save(self, commit=True):
        """Set settings to JSON field."""
        transport = super(BackendSettingsMixin, self).save(commit=False)
        transport._settings = {
            name: self.cleaned_data[name]
            for name in self.setting_field_names
        }
        if commit:
            transport.save()
        return transport


class TransportForm(BackendSettingsMixin, forms.ModelForm):
    """Transport model form."""

    service = forms.ChoiceField(choices=[])

    class Meta:
        fields = ("pattern", "service")
        model = models.Transport

    def __init__(self, *args, **kwargs):
        """Set backend list."""
        super(TransportForm, self).__init__(*args, **kwargs)
        self.fields["service"].choices = backends.manager.get_backend_list()
        settings = backends.manager.get_all_backend_settings()
        for name, backend_settings in settings.items():
            self.inject_backend_settings(name, backend_settings)

    @property
    def setting_fields(self):
        return [self[name] for name in self.setting_field_names]

    def _clean_fields(self):
        """Make backend settings required."""
        backend_name = self.data.get("service")
        backend_settings = backends.manager.get_backend_settings(backend_name)
        for name, field in self.fields.items():
            if name.startswith("{}_".format(backend_name)):
                name = name.replace("{}_".format(backend_name), "")
                for setting in backend_settings:
                    if setting["name"] == name:
                        break
                if setting.get("required", True):
                    field.required = True
        return super(TransportForm, self)._clean_fields()

    def clean(self):
        """Check values."""
        cleaned_data = super(TransportForm, self).clean()
        if self.errors:
            return cleaned_data
        self.clean_backend_fields(cleaned_data["service"])
        return cleaned_data
