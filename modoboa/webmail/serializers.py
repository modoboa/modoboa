"""Webmail serializers."""

from django.utils.translation import gettext as _
from django.utils import timezone

from rest_framework import serializers

from modoboa.lib import email_utils
from modoboa.webmail import constants, models
from modoboa.webmail.lib import imapheader, signature
from modoboa.webmail.lib.imaputils import get_imapconnector


class GlobalParametersSerializer(serializers.Serializer):
    max_attachment_size = serializers.CharField(default="2048")

    imap_server = serializers.CharField(default="127.0.0.1")
    imap_secured = serializers.BooleanField(default=False)
    imap_port = serializers.IntegerField(default=143)

    smtp_server = serializers.CharField(default="127.0.0.1")
    smtp_secured_mode = serializers.ChoiceField(
        default=constants.SmtpConnectionMode.NONE.value,
        choices=constants.SMTP_CONNECTION_MODES,
    )
    smtp_port = serializers.IntegerField(default=25)
    smtp_authentication = serializers.BooleanField(default=False)

    scheduling_smtp_server = serializers.CharField(default="127.0.0.1")
    scheduling_smtp_secured_mode = serializers.ChoiceField(
        default=constants.SmtpConnectionMode.NONE.value,
        choices=constants.SMTP_CONNECTION_MODES,
    )
    scheduling_smtp_port = serializers.IntegerField(default=25)


class UserPreferencesSerializer(serializers.Serializer):
    displaymode = serializers.ChoiceField(
        default=constants.DisplayMode.PLAIN.value, choices=constants.DISPLAY_MODES
    )
    enable_links = serializers.BooleanField(default=False)
    messages_per_page = serializers.IntegerField(default=40)
    refresh_interval = serializers.IntegerField(default=300)
    mboxes_col_width = serializers.IntegerField(default=200)

    trash_folder = serializers.CharField(default="Trash")
    sent_folder = serializers.CharField(default="Sent")
    drafts_folder = serializers.CharField(default="Drafts")
    junk_folder = serializers.CharField(default="Junk")

    editor = serializers.ChoiceField(
        default=constants.DisplayMode.PLAIN.value, choices=constants.DISPLAY_MODES
    )
    signature = serializers.CharField(required=False)
    signature = serializers.CharField(required=False)


class UserMailboxSerializer(serializers.Serializer):

    name = serializers.CharField()
    path = serializers.CharField(required=False)
    label = serializers.CharField()
    type = serializers.ChoiceField(choices=constants.MAILBOX_TYPES)
    unseen = serializers.IntegerField(default=0)
    removed = serializers.BooleanField(default=False)
    sub = serializers.SerializerMethodField()

    def get_sub(self, obj):
        if "sub" in obj:
            return UserMailboxSerializer(obj["sub"], many=True).data
        return None


class UserMailboxQuotaSerializer(serializers.Serializer):

    usage = serializers.IntegerField(source="quota_usage")
    current = serializers.IntegerField(source="quota_current")
    limit = serializers.IntegerField(source="quota_limit")


class UserMailboxUnseenSerializer(serializers.Serializer):

    counter = serializers.IntegerField()


class UserMailboxesSerializer(serializers.Serializer):

    mailboxes = UserMailboxSerializer(many=True)
    hdelimiter = serializers.CharField()


class UserMailboxInputSerializer(serializers.Serializer):

    name = serializers.CharField()
    parent_mailbox = serializers.CharField(required=False)


class UserMailboxUpdateSerializer(UserMailboxInputSerializer):

    oldname = serializers.CharField()


class EmailAddressSerializer(serializers.Serializer):
    fulladdress = serializers.CharField()
    address = serializers.CharField()
    name = serializers.CharField(required=False)
    contact_id = serializers.IntegerField(required=False)


class AttachmentSerializer(serializers.Serializer):
    name = serializers.CharField()
    partnum = serializers.CharField()


class AttachmentUploadSerializer(serializers.Serializer):
    attachment = serializers.FileField()


class UploadedAttachmentSerializer(serializers.Serializer):

    tmpname = serializers.CharField()
    fname = serializers.CharField()


class EmailHeadersSerializer(serializers.Serializer):

    imapid = serializers.CharField()
    subject = serializers.SerializerMethodField()
    from_address = serializers.SerializerMethodField()
    recipients = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    size = serializers.IntegerField()
    answered = serializers.BooleanField(default=False)
    attachments = serializers.BooleanField(default=False)
    forwarded = serializers.BooleanField(default=False)
    flagged = serializers.BooleanField(default=False)
    style = serializers.CharField(required=False)

    scheduled_id = serializers.IntegerField(
        source=constants.CUSTOM_HEADER_SCHEDULED_ID, required=False
    )
    scheduled_datetime = serializers.SerializerMethodField(required=False)
    scheduled_datetime_raw = serializers.CharField(
        source=constants.CUSTOM_HEADER_SCHEDULED_DATETIME, required=False
    )

    def get_subject(self, obj) -> str:
        if "Subject" in obj:
            return imapheader.parse_subject(obj["Subject"])
        return ""

    def get_from_address(self, obj):
        if "From" in obj:
            return imapheader.parse_address(obj["From"])
        return ""

    def get_recipients(self, obj):
        if "To" in obj:
            return imapheader.parse_address_list(obj["To"])
        return ""

    def get_date(self, obj) -> str:
        if "Date" in obj:
            return imapheader.parse_date(obj["Date"])
        return ""

    def get_scheduled_datetime(self, obj) -> str:
        if constants.CUSTOM_HEADER_SCHEDULED_DATETIME in obj:
            return imapheader.parse_scheduled_datetime(
                obj[constants.CUSTOM_HEADER_SCHEDULED_DATETIME]
            )
        return ""


class PaginatedEmailListSerializer(serializers.Serializer):

    count = serializers.IntegerField()
    first_index = serializers.IntegerField()
    last_index = serializers.IntegerField()
    prev_page = serializers.IntegerField()
    next_page = serializers.IntegerField()
    results = EmailHeadersSerializer(many=True)


class EmailSerializer(serializers.Serializer):

    subject = serializers.CharField()
    from_address = EmailAddressSerializer(source="From")
    to = EmailAddressSerializer(source="To", many=True)
    cc = EmailAddressSerializer(source="Cc", many=True, required=False)
    body = serializers.CharField()
    date = serializers.CharField(source="Date")
    message_id = serializers.CharField(source="Message_ID", required=False)
    reply_to = serializers.EmailField(source="Reply_To", required=False)
    attachments = serializers.SerializerMethodField()

    scheduled_datetime = serializers.DateTimeField(
        source=constants.CUSTOM_HEADER_SCHEDULED_DATETIME.replace("-", "_"),
        required=False,
    )

    def get_attachments(self, email):
        result = []
        if email.attachments:
            for partnum, name in email.attachments.items():
                data = {"name": name, "partnum": partnum}
                result.append(data)
        return result


class MoveSelectionSerializer(serializers.Serializer):

    source = serializers.CharField()
    destination = serializers.CharField(required=False)
    selection = serializers.ListField(child=serializers.CharField())

    def validate_source(self, value):
        if value == constants.MAILBOX_NAME_SCHEDULED:
            raise serializers.ValidationError(
                _("Moving scheduled messages is forbidden")
            )
        return value

    def validate_selection(self, value):
        return [item for item in value if item.isdigit()]


class FlagSelectionSerializer(serializers.Serializer):

    mailbox = serializers.CharField()
    selection = serializers.ListField(child=serializers.CharField())
    status = serializers.ChoiceField(
        choices=[
            ("read", "Read"),
            ("unread", "Unread"),
            ("flagged", "Flagged"),
            ("unflagged", "Unflagged"),
        ]
    )

    def validate_selection(self, value):
        return [item for item in value if item.isdigit()]


class ScheduledDatetimeMixin:
    """Mixin to inject scheduled_datetime logic into a serializer."""

    scheduled_datetime = serializers.DateTimeField(required=False)

    def validate_scheduled_datetime(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError(
                _("Only datetime in the future is allowed")
            )
        delta = value - timezone.now()
        if delta.total_seconds() < 60:
            raise serializers.ValidationError(
                _("Provived datetime must be one minute in the future at least")
            )
        return value


class SendEmailSerializer(ScheduledDatetimeMixin, serializers.Serializer):

    sender = serializers.EmailField()
    to = serializers.ListField(child=serializers.EmailField())
    cc = serializers.ListField(child=serializers.EmailField(), required=False)
    bcc = serializers.ListField(child=serializers.EmailField(), required=False)
    subject = serializers.CharField(required=False)
    body = serializers.CharField(required=False)

    in_reply_to = serializers.CharField(required=False)

    scheduled_datetime = serializers.DateTimeField(required=False)

    def validate_to(self, value):
        return email_utils.prepare_addresses(value, "envelope")

    def validate_cc(self, value):
        return email_utils.prepare_addresses(value, "envelope")

    def validate_bcc(self, value):
        return email_utils.prepare_addresses(value, "envelope")


class ComposeSessionSerializer(serializers.Serializer):

    attachments = UploadedAttachmentSerializer(many=True, required=False)
    uid = serializers.CharField()
    signature = serializers.SerializerMethodField()
    editor_format = serializers.SerializerMethodField()

    def get_editor_format(self, obj):
        return self.context["request"].user.parameters.get_value("editor")

    def get_signature(self, obj):
        return str(signature.EmailSignature(self.context["request"].user))


class AllowedSenderSerializer(serializers.Serializer):

    address = serializers.EmailField()


class ScheduledMessageSerializer(ScheduledDatetimeMixin, serializers.ModelSerializer):

    class Meta:
        model = models.ScheduledMessage
        fields = ["error", "scheduled_datetime"]
        read_only_fields = ["error"]

    def update(self, instance, validated_data):
        instance = super().update(instance, validated_data)
        message = instance.to_email_message()
        with get_imapconnector(self.context["request"]) as imapc:
            imapc.delete_mail(constants.MAILBOX_NAME_SCHEDULED, instance.imap_uid)
            instance.imap_uid = imapc.push_mail(
                constants.MAILBOX_NAME_SCHEDULED, message.message()
            )
            instance.save()
        return instance
