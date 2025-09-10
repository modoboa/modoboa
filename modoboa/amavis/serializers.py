"""Amavis serializers."""

from django.utils.translation import gettext as _

from rest_framework import serializers

from modoboa.amavis import models


class GlobalParametersSerializer(serializers.Serializer):

    localpart_is_case_sensitive = serializers.BooleanField(default=False)
    recipient_delimiter = serializers.CharField(default="", allow_blank=True)
    max_messages_age = serializers.IntegerField(default=14)
    released_msgs_cleanup = serializers.BooleanField(default=False)
    am_pdp_mode = serializers.ChoiceField(
        choices=[("inet", "inet"), ("unix", "unix")],
        default="unix",
    )
    am_pdp_host = serializers.CharField(default="localhost", required=False)
    am_pdp_port = serializers.IntegerField(default=9998, required=False)
    am_pdp_socket = serializers.CharField(
        default="/var/amavis/amavisd.sock", required=False
    )
    user_can_release = serializers.BooleanField(default=False)
    self_service = serializers.BooleanField(default=False)
    notifications_sender = serializers.EmailField(default="noreply@domain.tld")
    manual_learning = serializers.BooleanField(default=True)
    sa_is_local = serializers.BooleanField(default=True)
    default_user = serializers.CharField(default="amavis", required=False)
    spamd_address = serializers.CharField(default="127.0.0.1", required=False)
    spamd_port = serializers.IntegerField(default=783, required=False)
    domain_level_learning = serializers.BooleanField(default=False)
    user_level_learning = serializers.BooleanField(default=False)

    def validate(self, data):
        am_pdp_mode = data.get("am_pdp_mode")
        errors = {}
        error = _("This field is required")
        if am_pdp_mode == "inet":
            for name in ["am_pdp_host", "am_pdp_port"]:
                if name not in data:
                    errors[name] = error
        else:
            name = "am_pdp_socket"
            if name not in data:
                errors[name] = error
        manual_learning = data.get("manual_learning")
        if manual_learning:
            name = "default_user"
            if name not in data:
                errors[name] = error
            sa_is_local = data.get("sa_is_local")
            if sa_is_local:
                for name in ["spamd_address", "spamd_port"]:
                    if name not in data:
                        errors[name] = error
        if errors:
            raise serializers.ValidationError(errors)
        return data


class UserPreferencesSerializer(serializers.Serializer):

    messages_per_page = serializers.IntegerField(default=40)


class HeaderSerializer(serializers.Serializer):

    name = serializers.CharField()
    value = serializers.CharField()


class MessageHeadersSerializer(serializers.Serializer):

    headers = HeaderSerializer(many=True)


class MessageSerializer(serializers.Serializer):

    qtype = serializers.CharField()
    qreason = serializers.CharField()
    headers = HeaderSerializer(many=True)
    body = serializers.CharField()


class CompactMessageSerializer(serializers.Serializer):

    mailid = serializers.CharField()
    type = serializers.CharField()
    status = serializers.CharField()
    score = serializers.CharField()
    to_address = serializers.CharField()
    from_address = serializers.CharField()
    subject = serializers.CharField()
    datetime = serializers.DateTimeField()
    style = serializers.CharField(required=False)


class PaginatedMessageListSerializer(serializers.Serializer):

    count = serializers.IntegerField()
    first_index = serializers.IntegerField()
    last_index = serializers.IntegerField()
    prev_page = serializers.IntegerField()
    next_page = serializers.IntegerField()
    results = CompactMessageSerializer(many=True)


class MessageIdentifierSerializer(serializers.Serializer):

    mailid = serializers.CharField()
    rcpt = serializers.CharField()
    secret_id = serializers.CharField(required=False)


class MessageSelectionSerializer(serializers.Serializer):

    selection = MessageIdentifierSerializer(many=True)


class MarkMessageSelectionSerializer(MessageSelectionSerializer):

    type = serializers.CharField()
    database = serializers.CharField(required=False)


class PolicySerializer(serializers.ModelSerializer):

    class Meta:
        model = models.Policy
        fields = (
            "bypass_virus_checks",
            "bypass_spam_checks",
            "bypass_banned_checks",
            "spam_tag2_level",
            "spam_kill_level",
            "spam_subject_tag2",
        )
