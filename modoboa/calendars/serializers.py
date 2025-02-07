"""Calendar serializers."""

from django.utils.translation import gettext as _

from rest_framework import serializers

from modoboa.admin import models as admin_models
from modoboa.lib import fields as lib_fields

from . import backends
from . import models


class CalDAVCalendarMixin:
    """Mixin for calendar serializers."""

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
    start = serializers.DateTimeField()
    end = serializers.DateTimeField()
    allDay = serializers.BooleanField(default=False)
    color = serializers.CharField(read_only=True)
    description = serializers.CharField(required=False)

    attendees = AttendeeSerializer(many=True, required=False)


class ROEventSerializer(EventSerializer):
    """Event serializer for read operations."""

    def __init__(self, *args, **kwargs):
        """Set calendar field based on type."""
        calendar_type = kwargs.pop("calendar_type", None)
        super().__init__(*args, **kwargs)
        self.fields["calendar"] = (
            SharedCalendarSerializer()
            if calendar_type != "user"
            else UserCalendarSerializer()
        )


class WritableEventSerializer(EventSerializer):
    """Event serializer for write operations."""

    calendar = serializers.PrimaryKeyRelatedField(
        queryset=models.UserCalendar.objects.none()
    )
    new_calendar_type = serializers.CharField(required=False)

    def __init__(self, *args, **kwargs):
        """Set calendar list."""
        calendar_type = kwargs.pop("calendar_type")
        super(EventSerializer, self).__init__(*args, **kwargs)
        self.update_calendar_field(calendar_type)

    def update_calendar_field(self, calendar_type):
        """Update field based on given type."""
        user = self.context["request"].user
        if user.is_anonymous:
            return
        if calendar_type == "user":
            self.fields["calendar"].queryset = models.UserCalendar.objects.filter(
                mailbox__user=user
            )
        elif hasattr(user, "mailbox"):
            self.fields["calendar"].queryset = models.SharedCalendar.objects.filter(
                domain=user.mailbox.domain
            )

    def validate(self, data):
        """Make sure dates are present with allDay flag."""
        errors = {}
        if "allDay" in data:
            if "start" not in data:
                errors["start"] = _("This field is required.")
            if "end" not in data:
                errors["end"] = _("This field is required.")
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

    def create(self, validated_data):
        """Create access rule."""
        mailbox = validated_data.pop("mailbox")
        rule = models.AccessRule(**validated_data)
        rule.mailbox_id = mailbox["pk"]
        rule.save()
        return rule

    def update(self, instance, validated_data):
        """Update access rule."""
        mailbox = validated_data.pop("mailbox")
        for key, value in validated_data.items():
            setattr(instance, key, value)
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


class GlobalParametersSerializer(serializers.Serializer):
    """A serializer for global parameters."""

    server_location = serializers.CharField(default="")
    rights_file_path = serializers.CharField(default="/etc/radicale/rights")
    allow_calendars_administration = serializers.BooleanField(default=False)
    max_ics_file_size = serializers.CharField(default="10240")
