"""Models for the limits extensions."""

from django.conf import settings
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.functional import cached_property
from django.utils.translation import ugettext as _

from modoboa.core import models as core_models
from . import lib, utils


class ObjectLimitMixin(object):
    """Common methods."""

    @property
    def label(self):
        """Return display name."""
        return self.definition["label"]

    @property
    def type(self):
        """Return limit type."""
        return self.definition.get("type", "count")

    @property
    def usage(self):
        """Return current limit usage in %."""
        if self.max_value < 0:
            return -1
        if self.max_value == 0:
            return 100
        return int(float(self.current_value) / self.max_value * 100)

    def is_exceeded(self, count=1, instance=None):
        """Check if limit will be reached if we add this object."""
        if self.type == "count":
            if self.max_value == -1:
                return False
            return self.current_value + count > self.max_value
        if self.max_value == 0 or instance is None:
            return False
        field = self.definition["field"]
        value = getattr(instance, field)
        if value == 0:
            # Do not allow unlimited value
            raise lib.BadLimitValue(
                _("You're not allowed to define unlimited values"))
        try:
            old_value = instance._loaded_values[field]
        except (AttributeError, KeyError):
            old_value = 0
        return self.current_value + (value - old_value) > self.max_value

    def __str__(self):
        """Display current usage."""
        if self.max_value == -1:
            return _("unlimited")
        return "{}%".format(self.usage)


@python_2_unicode_compatible
class UserObjectLimit(ObjectLimitMixin, models.Model):
    """Object level limit."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    name = models.CharField(max_length=254)
    content_type = models.ForeignKey("contenttypes.ContentType",
                                     on_delete=models.CASCADE)
    max_value = models.IntegerField(default=0)

    class Meta(object):
        unique_together = (("user", "name"), )

    @property
    def definition(self):
        """Return the definition of this limit."""
        for name, tpl in utils.get_user_limit_templates():
            if name == self.name:
                return tpl
        return None

    @property
    def current_value(self):
        """Return the current number of objects."""
        condition = (
            self.type == "count" and
            "extra_filters" not in self.definition)
        if condition:
            return core_models.ObjectAccess.objects.filter(
                user=self.user, is_owner=True,
                content_type=self.content_type).count()
        id_list = core_models.ObjectAccess.objects.filter(
            user=self.user, is_owner=True,
            content_type=self.content_type).values_list("object_id", flat=True)
        model_class = self.content_type.model_class()
        if self.type == "count":
            return model_class.objects.filter(
                pk__in=id_list, **self.definition["extra_filters"]).count()
        qset = model_class.objects.filter(pk__in=id_list)
        if not qset.exists():
            return 0
        return qset.aggregate(
            total=models.Sum(self.definition["field"]))["total"]

    @property
    def label(self):
        """Return display name."""
        return self.definition["label"]

    @cached_property
    def usage(self):
        """Return current limit usage in %."""
        if self.max_value < 0:
            return -1
        if self.max_value == 0:
            return 100
        return int(float(self.current_value) / self.max_value * 100)

    def __str__(self):
        """Display current usage."""
        if self.max_value == -1:
            return _("unlimited")
        return "{}%".format(self.usage)


class DomainObjectLimit(ObjectLimitMixin, models.Model):
    """Per-domain limits on object creation."""

    domain = models.ForeignKey("admin.Domain", on_delete=models.CASCADE)
    name = models.CharField(max_length=254)
    max_value = models.IntegerField(default=0)

    class Meta(object):
        unique_together = (("domain", "name"), )

    @property
    def definition(self):
        """Return the definition of this limit."""
        for name, tpl in utils.get_domain_limit_templates():
            if name == self.name:
                return tpl
        return None

    @property
    def current_value(self):
        """Return the current number of objects."""
        definition = self.definition
        if not definition:
            raise RuntimeError("Bad limit {}".format(self.name))
        relation = getattr(self.domain, definition["relation"])
        if "extra_filters" in definition:
            relation = relation.filter(**definition["extra_filters"])
        return relation.count()
