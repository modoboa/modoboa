"""Parameters management."""

import copy
from typing import Optional

from rest_framework.fields import empty

from modoboa.lib import exceptions, form_utils, signals
from modoboa.lib.sysutils import guess_extension_name


class NotDefined(exceptions.ModoboaException):
    """Custom exception for undefined parameters."""

    http_code = 404

    def __init__(self, app, name=None):
        self.app = app
        self.name = name

    def __str__(self):
        if self.name is None:
            return f"Application {self.app} not registered"
        return f"Parameter {self.name} not defined for app {self.app}"


class Registry:
    """A registry for parameters."""

    def __init__(self):
        """Constructor."""
        self._registry = {"global": {}, "user": {}}
        self._registry2 = {"global": {}, "user": {}}

    def add(self, level, formclass, label):
        """Add a new class containing parameters."""
        self._registry[level][formclass.app] = {
            "label": label,
            "formclass": formclass,
            "defaults": {},
        }

    def add2(
        self,
        level: str,
        app: str,
        label: str,
        structure: dict,
        serializer_class,
        is_extension: bool = False,
    ) -> None:
        """Add new parameters for given app and level."""
        self._registry2[level][app] = {
            "label": label,
            "structure": structure,
            "serializer_class": serializer_class,
            "is_extension": is_extension,
            "defaults": {},
        }

    def _load_default_values(self, level):
        """Load default values."""
        for _app, data in list(self._registry[level].items()):
            form = data["formclass"](load_values_from_db=False)
            for name, field in list(form.fields.items()):
                if isinstance(field, form_utils.SeparatorField):
                    continue
                data["defaults"][name] = field.initial
        for data in list(self._registry2[level].values()):
            serializer = data["serializer_class"]()
            for name, field in list(serializer.fields.items()):
                if field.default is not empty:
                    data["defaults"][name] = field.default

    def get_applications(self, level):
        """Return all applications registered for level."""
        result = [
            {
                "name": key,
                "label": value["label"],
                "is_extension": value["is_extension"],
            }
            for key, value in self._registry2[level].items()
        ]
        return result

    def get_label(self, level: str, app: str) -> str:
        return self._registry2[level][app]["label"]

    def get_forms(self, level, *args, **kwargs):
        """Return form instances for all app of the given level."""
        sorted_apps = []
        first_app = kwargs.pop("first_app", "core")
        if first_app in self._registry[level]:
            sorted_apps.append(first_app)
        sorted_apps += sorted(
            (a for a in self._registry[level] if a != first_app),
            key=lambda a: self._registry[level][a]["label"],
        )
        result = []
        for app in sorted_apps:
            data = self._registry[level][app]
            if not data["formclass"].has_access(**kwargs):
                continue
            result.append(
                {
                    "app": app,
                    "label": data["label"],
                    "form": data["formclass"](*args, **kwargs),
                }
            )
        return result

    def get_serializer_class(self, level: str, app: str):
        """Return serializer class for given level and app."""
        if app not in self._registry2[level]:
            raise NotDefined(app)
        return self._registry2[level][app]["serializer_class"]

    def get_structure(self, level: str, for_app: Optional[str] = None) -> list:
        """Return fields structure."""
        result = []
        for app, fields in list(self._registry2[level].items()):
            if for_app and for_app != app:
                continue
            serializer = fields["serializer_class"]()
            for _section, sconfig in list(fields["structure"].items()):
                item = {
                    "label": sconfig["label"],
                    "display": sconfig.get("display", ""),
                    "parameters": [],
                }
                for name, config in list(sconfig["params"].items()):
                    data = {
                        "name": name,
                        "label": config["label"],
                        "help_text": config.get("help_text", ""),
                        "display": config.get("display", ""),
                    }
                    if config.get("separator"):
                        data["widget"] = "SeparatorField"
                    else:
                        field = serializer.fields[name]
                        if config.get("password"):
                            data["widget"] = "PasswordField"
                        else:
                            data["widget"] = field.__class__.__name__
                            if data["widget"] == "ChoiceField":
                                data["choices"] = [
                                    {"text": value, "value": key}
                                    for key, value in field.choices.items()
                                ]
                    item["parameters"].append(data)
                result.append(item)
        return result

    def exists(self, level: str, app: str, parameter: Optional[str] = None) -> bool:
        """Check if parameter exists."""
        parameters = self._registry[level]
        result = app in parameters
        if parameter:
            result = result and parameter in parameters[app]["defaults"]
        if result:
            return result
        parameters = self._registry2[level]
        result = app in parameters
        if parameter:
            result = result and parameter in parameters[app]["defaults"]
        return result

    def get_default(self, level: str, app: str, parameter: str):
        """Retrieve default value for parameter."""
        if (
            app in self._registry[level]
            and parameter in self._registry[level][app]["defaults"]
        ):
            return self._registry[level][app]["defaults"][parameter]
        if (
            app in self._registry2[level]
            and parameter in self._registry2[level][app]["defaults"]
        ):
            return self._registry2[level][app]["defaults"][parameter]
        raise NotDefined(app)

    def get_defaults(self, level: str, app: str) -> dict:
        """Retrieve default values for application."""
        if app in self._registry[level]:
            return self._registry[level][app]["defaults"]
        if app in self._registry2[level]:
            return self._registry2[level][app]["defaults"]
        raise NotDefined(app)


registry = Registry()


class Manager:
    """A manager for parameters."""

    def __init__(self, level: str, parameters) -> None:
        """Constructor."""
        self._level = level
        self._parameters = parameters
        registry._load_default_values(level)

    def get_value(self, parameter, app=None, raise_exception=True):
        """Return the value associated to the specified parameter."""
        if app is None:
            app = guess_extension_name()
        # Compat. with the old way...
        parameter = parameter.lower()
        try:
            default = registry.get_default(self._level, app, parameter)
        except NotDefined:
            if raise_exception:
                raise
            return None
        if app in self._parameters:
            return self._parameters[app].get(parameter, default)
        return default

    def get_values(self, app: Optional[str] = None):
        """Return all values for the given level/app."""
        if app is None:
            app = guess_extension_name()
        values = registry.get_defaults(self._level, app)
        for parameter, value in list(values.items()):
            if app in self._parameters:
                value = self._parameters[app].get(parameter, value)
            yield (parameter, value)

    def get_values_dict(self, app=None):
        """Return all values for the given app as a dictionary."""
        if app is None:
            app = guess_extension_name()
        values = registry.get_defaults(self._level, app)
        for parameter, value in list(values.items()):
            if app in self._parameters:
                values[parameter] = self._parameters[app].get(parameter, value)
        return values

    def set_value(self, parameter, value, app=None):
        """Set parameter for the given app."""
        if app is None:
            app = guess_extension_name()
        if not registry.exists(self._level, app, parameter):
            raise NotDefined(app, parameter)
        if app not in self._parameters:
            self._parameters[app] = copy.deepcopy(
                registry.get_defaults(self._level, app)
            )
        self._parameters[app][parameter] = value

    def set_values(self, values: dict, app: Optional[str] = None) -> None:
        """Set/update values for the given app."""
        if app is None:
            app = guess_extension_name()
        if not registry.exists(self._level, app):
            raise NotDefined(app)
        if app not in self._parameters:
            self._parameters[app] = copy.deepcopy(
                registry.get_defaults(self._level, app)
            )
        self._parameters[app].update(values)


def get_localconfig():
    """Retrieve current LocalConfig instance."""
    from modoboa.core import models as core_models

    request = signals.get_request()
    if request:
        return request.localconfig
    return core_models.LocalConfig.objects.first()


def get_global_parameter(name, app=None, **kwargs):
    """Retrieve a global parameter.

    This is a shortcut to use when a LocalConfig instance is not
    available (ie. when no request object is available).

    A ``NotDefined`` exception if the parameter doesn't exist.

    :param name: the parameter's name
    :param app: the application owning the parameter
    :return: the corresponding value
    """
    if app is None:
        app = guess_extension_name()
    return get_localconfig().parameters.get_value(name, app=app, **kwargs)


def get_global_parameters(app, **kwargs):
    """Retrieve global parameters of a given app.

    This is a shortcut to use when a LocalConfig instance is not
    available (ie. when no request object is available).

    A ``NotDefined`` exception if the parameter doesn't exist.

    :param name: the parameter's name
    :param app: the application owning the parameter
    :return: the corresponding value

    """
    return get_localconfig().parameters.get_values(app, **kwargs)


def apply_to_django_settings():
    """Apply global parameters to Django settings module."""
    for form in registry.get_forms("global"):
        form["form"].to_django_settings()
