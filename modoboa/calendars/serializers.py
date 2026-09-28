"""Calendar serializers."""

import re

from django.db.models import Q
from django.utils.translation import gettext as _

from rest_framework import serializers

from modoboa.admin import models as admin_models
from modoboa.lib import fields as lib_fields

from . import backends
from . import models
from . import rights

#: Scope of a modification made on an occurrence of a recurring event
RECURRENCE_SCOPES = ("occurrence", "series")


class CalDAVCalendarMixin:
    """Mixin for calendar serializers."""

    def validate_name(self, value):
        """Reject names that could break out of the Radicale rights file."""
        models.calendar_name_validator(value)
        return value

    def check_name_is_free(self, queryset, name):
        """Make sure no other calendar of queryset is named name.

        Comparison ignores case, like most database collations.
        """
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)
        if queryset.filter(name__iexact=name).exists():
            raise serializers.ValidationError(
                {"name": _("A calendar with this name already exists.")}
            )

    def create_remote_calendar(self, calendar):
        """Create caldav calendar."""
        request = self.context["request"]
        backend = backends.get_backend_from_request("caldav_", request)
        backend.create_calendar(calendar.encoded_url)

    def update_remote_calendar(self, calendar):
        """Update caldav calendar."""
        request = self.context["request"]
        backend = backends.get_backend_from_request("caldav_", request)
        backend.update_calendar(calendar)


class UserCalendarSerializer(CalDAVCalendarMixin, serializers.ModelSerializer):
    """User calendar serializer."""

    class Meta:
        model = models.UserCalendar
        fields = ("pk", "name", "color", "path", "full_url", "share_url")
        read_only_fields = ("pk", "path", "full_url", "share_url")

    def validate(self, data):
        """Names are unique per owner."""
        if "name" in data:
            mailbox = (
                self.instance.mailbox
                if self.instance
                else self.context["request"].user.mailbox
            )
            self.check_name_is_free(
                models.UserCalendar.objects.filter(mailbox=mailbox), data["name"]
            )
        return data

    def create(self, validated_data):
        """Use current user."""
        user = self.context["request"].user
        calendar = models.UserCalendar.objects.create(
            mailbox=user.mailbox, **validated_data
        )
        self.create_remote_calendar(calendar)
        return calendar

    def update(self, instance, validated_data):
        """Update calendar."""
        old_name = instance.name
        old_color = instance.color
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.save()
        if old_name != instance.name or old_color != instance.color:
            self.update_remote_calendar(instance)
        return instance


class SharedWithMeCalendarSerializer(serializers.ModelSerializer):
    """A user calendar shared with the current user by an access rule.

    The grantee chooses the color and the visibility of the calendar.
    The share URL is not returned: its token belongs to the owner.
    """

    pk = serializers.IntegerField(source="calendar.pk", read_only=True)
    name = serializers.CharField(source="calendar.name", read_only=True)
    full_url = serializers.CharField(source="calendar.full_url", read_only=True)
    owner = lib_fields.DRFEmailFieldUTF8(
        source="calendar.mailbox.full_address", read_only=True
    )

    class Meta:
        model = models.AccessRule
        fields = ("pk", "name", "color", "visible", "full_url", "owner", "write")
        read_only_fields = ("write",)

    def validate_color(self, value):
        """An empty value restores the color chosen by the owner."""
        if value and not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
            raise serializers.ValidationError(_("Invalid color"))
        return value

    def to_representation(self, instance):
        data = super().to_representation(instance)
        data["color"] = instance.color or instance.calendar.color
        return data


class EventCalendarSerializer(serializers.ModelSerializer):
    """Calendar of an event.

    The calendar can be shared with the current user, so its share URL
    is not returned.
    """

    class Meta:
        model = models.UserCalendar
        fields = ("pk", "name", "color")
        read_only_fields = fields


class DomainSerializer(serializers.ModelSerializer):
    """Domain serializer."""

    pk = serializers.IntegerField()
    name = serializers.CharField()

    class Meta:
        model = admin_models.Domain
        fields = ("pk", "name")
        read_only_fields = (
            "pk",
            "name",
        )


class SharedCalendarSerializer(CalDAVCalendarMixin, serializers.ModelSerializer):
    """Shared calendar serializer."""

    domain = DomainSerializer()

    class Meta:
        model = models.SharedCalendar
        fields = ("pk", "name", "color", "path", "domain", "full_url", "share_url")
        read_only_fields = ("pk", "path", "full_url", "share_url")

    def validate_domain(self, value):
        """Ensure the target domain is one the requester administers.

        Without this check any admin could create or move a shared calendar
        under a domain they do not manage (cross-tenant resource creation).
        """
        user = self.context["request"].user
        if (
            not admin_models.Domain.objects.get_for_admin(user)
            .filter(pk=value["pk"])
            .exists()
        ):
            raise serializers.ValidationError(_("Permission denied."))
        return value

    def validate(self, data):
        """Names are unique per domain."""
        if "name" in data:
            domain_pk = (
                data["domain"]["pk"] if "domain" in data else self.instance.domain_id
            )
            self.check_name_is_free(
                models.SharedCalendar.objects.filter(domain_id=domain_pk),
                data["name"],
            )
        return data

    def create(self, validated_data):
        """Create shared calendar."""
        domain = validated_data.pop("domain")
        calendar = models.SharedCalendar(**validated_data)
        calendar.domain_id = domain["pk"]
        calendar.save()
        self.create_remote_calendar(calendar)
        return calendar

    def update(self, instance, validated_data):
        """Update calendar."""
        domain = validated_data.pop("domain")
        old_name = instance.name
        old_color = instance.color
        for key, value in validated_data.items():
            setattr(instance, key, value)
        instance.domain_id = domain["pk"]
        instance.save()
        if old_name != instance.name or old_color != instance.color:
            self.update_remote_calendar(instance)
        return instance


class AttendeeSerializer(serializers.Serializer):
    """Attendee serializer."""

    display_name = serializers.CharField()
    email = serializers.EmailField()


class EventSerializer(serializers.Serializer):
    """Base event serializer (fullcalendar output)."""

    id = serializers.CharField(read_only=True)
    title = serializers.CharField()
    start = serializers.DateTimeField(required=False)
    end = serializers.DateTimeField(required=False)
    allDay = serializers.BooleanField(default=False)
    color = serializers.CharField(read_only=True)
    description = serializers.CharField(required=False, allow_blank=True)

    attendees = AttendeeSerializer(many=True, required=False)
    recurrence_id = serializers.CharField(required=False, allow_null=True)


class RecurrenceSerializer(serializers.Serializer):
    """Identify an occurrence of a recurring event and the scope of an action."""

    recurrence_id = serializers.CharField(required=False, allow_null=True)
    scope = serializers.ChoiceField(
        choices=RECURRENCE_SCOPES, required=False, allow_null=True
    )

    def validate_recurrence_id(self, value):
        if not value:
            return None
        try:
            return backends.parse_recurrence_id(value)
        except ValueError as exc:
            raise serializers.ValidationError(_("Invalid recurrence id")) from exc

    def validate(self, data):
        data = super().validate(data)
        if data.get("recurrence_id") and not data.get("scope"):
            raise serializers.ValidationError({"scope": _("This field is required.")})
        return data


class ROEventSerializer(EventSerializer):
    """Event serializer for read operations."""

    def __init__(self, *args, **kwargs):
        """Set calendar field based on type."""
        calendar_type = kwargs.pop("calendar_type", None)
        super().__init__(*args, **kwargs)
        self.fields["calendar"] = (
            SharedCalendarSerializer()
            if calendar_type != "user"
            else EventCalendarSerializer()
        )


class WritableEventSerializer(EventSerializer):
    """Event serializer for write operations."""

    calendar = serializers.PrimaryKeyRelatedField(
        queryset=models.UserCalendar.objects.none()
    )
    new_calendar_type = serializers.CharField(required=False)

    start_date = serializers.DateField(required=False)
    end_date = serializers.DateField(required=False)

    scope = serializers.ChoiceField(
        choices=RECURRENCE_SCOPES, required=False, allow_null=True
    )

    def __init__(self, *args, **kwargs):
        """Set calendar list."""
        calendar_type = kwargs.pop("calendar_type")
        super().__init__(*args, **kwargs)
        self.update_calendar_field(calendar_type)

    def update_calendar_field(self, calendar_type):
        """Update field based on given type."""
        user = self.context["request"].user
        if user.is_anonymous:
            return
        if calendar_type == "user":
            shared_calendars = (
                rights.get_rules_shared_with(user).filter(write=True).values("calendar")
            )
            self.fields["calendar"].queryset = models.UserCalendar.objects.filter(
                Q(mailbox__user=user) | Q(pk__in=shared_calendars)
            )
        elif hasattr(user, "mailbox"):
            self.fields["calendar"].queryset = models.SharedCalendar.objects.filter(
                domain=user.mailbox.domain
            )

    def validate_recurrence_id(self, value):
        return RecurrenceSerializer().validate_recurrence_id(value)

    def validate(self, data):
        """Make sure dates are present with allDay flag."""
        RecurrenceSerializer().validate(data)
        errors = {}
        if data.get("allDay", False):
            mandatory_fields = ["start_date", "end_date"]
        else:
            mandatory_fields = ["start", "end"]
        for field in mandatory_fields:
            if not data.get(field):
                errors[field] = _("This field is required.")
        if errors:
            raise serializers.ValidationError(errors)
        return data


class MailboxSerializer(serializers.ModelSerializer):
    """Mailbox serializer."""

    pk = serializers.IntegerField()
    full_address = lib_fields.DRFEmailFieldUTF8()

    class Meta:
        model = admin_models.Mailbox
        fields = ("pk", "full_address")
        read_only_fields = (
            "pk",
            "full_address",
        )


class AccessRuleSerializer(serializers.ModelSerializer):
    """AccessRule serializer."""

    mailbox = MailboxSerializer()

    class Meta:
        model = models.AccessRule
        fields = ("pk", "mailbox", "calendar", "read", "write")
        # Calendar comes from the URL (see AccessRuleViewSet)
        read_only_fields = ("calendar",)

    def validate_mailbox(self, value):
        calendar = self.context["calendar"]
        mailbox = (
            models.get_share_candidates(calendar.mailbox).filter(pk=value["pk"]).first()
        )
        if mailbox is None:
            raise serializers.ValidationError(_("Mailbox not found"))
        qset = models.AccessRule.objects.filter(calendar=calendar, mailbox=mailbox)
        if self.instance:
            qset = qset.exclude(pk=self.instance.pk)
        if qset.exists():
            raise serializers.ValidationError(
                _("An access rule already exists for this mailbox")
            )
        return value

    def validate(self, data):
        """Make sure the rule grants read access.

        A rule without any access grants nothing, and CalDAV clients
        can't display a calendar they can only write to.
        """
        read = data.get("read", self.instance.read if self.instance else False)
        if not read:
            raise serializers.ValidationError(
                {"read": _("Read access is required to share a calendar")}
            )
        return data

    def create(self, validated_data):
        """Create access rule."""
        mailbox = validated_data.pop("mailbox")
        rule = models.AccessRule(calendar=self.context["calendar"], **validated_data)
        rule.mailbox_id = mailbox["pk"]
        rule.save()
        return rule

    def update(self, instance, validated_data):
        """Update access rule."""
        # Absent from partial updates
        mailbox = validated_data.pop("mailbox", None)
        for key, value in validated_data.items():
            setattr(instance, key, value)
        if mailbox is not None:
            instance.mailbox_id = mailbox["pk"]
        instance.save()
        return instance


class CheckTokenSerializer(serializers.Serializer):
    """Serializer for the check_token action."""

    calendar = serializers.CharField()
    token = serializers.CharField()


class ImportFromFileSerializer(serializers.Serializer):
    """Serializer for the import_from_file action."""

    ics_file = serializers.FileField()


class RightsRequestSerializer(serializers.Serializer):
    """Rights requested by the Radicale server."""

    user = serializers.CharField()


class RightsSerializer(serializers.Serializer):
    """Rights of a user on collections owned by someone else."""

    admin_domains = serializers.ListField(child=serializers.CharField())
    managed_domains = serializers.ListField(child=serializers.CharField())
    shares = serializers.DictField(child=serializers.CharField())


class GlobalParametersSerializer(serializers.Serializer):
    """A serializer for global parameters."""

    server_location = serializers.CharField(default="")
    rights_file_path = serializers.CharField(default="/etc/radicale/rights")
    allow_calendars_administration = serializers.BooleanField(default=False)
    max_ics_file_size = serializers.CharField(default="10240")


HOUR_CHOICES = [(hour, f"{hour:02d}:00") for hour in range(25)]


class UserPreferencesSerializer(serializers.Serializer):
    """A serializer for user preferences."""

    working_hours_start = serializers.ChoiceField(choices=HOUR_CHOICES[:-1], default=9)
    working_hours_end = serializers.ChoiceField(choices=HOUR_CHOICES[1:], default=18)

    def validate(self, data):
        """Make sure working hours define a valid range."""
        if data["working_hours_start"] >= data["working_hours_end"]:
            raise serializers.ValidationError(
                {"working_hours_end": _("End of working hours must be after its start")}
            )
        return data
