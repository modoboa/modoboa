# coding: utf-8

"""Models for the limits extensions."""

from django.conf import settings
from django.db import models
from django.utils.encoding import python_2_unicode_compatible
from django.utils.functional import cached_property
from django.utils.translation import ugettext as _

from modoboa.core import models as core_models

from . import utils


class ObjectLimitMixin(object):
    """Common methods."""

    @property
    def label(self):
        """Return display name."""
        return self.definition["label"]

    @property
    def usage(self):
        """Return current limit usage in %."""
        if self.max_value < 0:
            return -1
        if self.max_value == 0:
            return 100
        return int(float(self.current_value) / self.max_value * 100)

    def is_exceeded(self, count=1):
        """Check if limit will be reached if we add count object(s)."""
        return self.current_value + 1 > self.max_value

    def __str__(self):
        """Display current usage."""
        if self.max_value == -1:
            return _("unlimited")
        return "{}%".format(self.usage)


@python_2_unicode_compatible
class UserObjectLimit(ObjectLimitMixin, models.Model):
    """Object level limit."""

    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    name = models.CharField(max_length=254)
    content_type = models.ForeignKey("contenttypes.ContentType")
    max_value = models.IntegerField(default=0)

    class Meta:
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
        if "extra_filters" not in self.definition:
            return core_models.ObjectAccess.objects.filter(
                user=self.user, is_owner=True,
                content_type=self.content_type).count()
        id_list = core_models.ObjectAccess.objects.filter(
            user=self.user, is_owner=True,
            content_type=self.content_type).values_list("object_id", flat=True)
        model_class = self.content_type.model_class()
        return model_class.objects.filter(
            pk__in=id_list, **self.definition["extra_filters"]).count()

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

    def is_exceeded(self, count=1):
        """Check if limit will be reached if we add count object(s)."""
        return self.current_value + 1 > self.max_value

    def __str__(self):
        """Display current usage."""
        if self.max_value == -1:
            return _("unlimited")
        return "{}%".format(self.usage)


class DomainObjectLimit(ObjectLimitMixin, models.Model):
    """Per-domain limits on object creation."""

    domain = models.ForeignKey("admin.Domain")
    name = models.CharField(max_length=254)
    max_value = models.IntegerField(default=0)

    class Meta:
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
