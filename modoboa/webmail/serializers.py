"""Webmail serializers."""

from django.utils.translation import gettext as _
from django.utils import timezone

from rest_framework import serializers

from modoboa.lib import email_utils
from modoboa.webmail import constants, models
from modoboa.webmail.lib import imapheader, signature
from modoboa.webmail.lib.imaputils import get_imapconnector
from modoboa.webmail.lib.utils import allowed_sender_addresses, create_message


class GlobalParametersSerializer(serializers.Serializer):
    max_attachment_size = serializers.CharField(default="2048")
    max_attachments_total_size = serializers.CharField(default="10M")
    max_attachments_count = serializers.IntegerField(default=10, min_value=1)

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


class SubscriptionNodeSerializer(serializers.Serializer):

    name = serializers.CharField()
    label = serializers.CharField()
    subscribed = serializers.BooleanField()
    sub = serializers.SerializerMethodField()

    def get_sub(self, obj):
        return SubscriptionNodeSerializer(obj.get("sub", []), many=True).data


class SubscriptionsSerializer(serializers.Serializer):

    mailboxes = SubscriptionNodeSerializer(many=True)
    hdelimiter = serializers.CharField()


class SubscriptionChangeSerializer(serializers.Serializer):

    name = serializers.CharField()
    subscribed = serializers.BooleanField()


class SubscriptionUpdateSerializer(serializers.Serializer):

    changes = SubscriptionChangeSerializer(many=True)


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
    # Top-level folders send an empty parent: accept it (treated as "no
    # parent" by the viewsets) instead of rejecting it as blank.
    parent_mailbox = serializers.CharField(required=False, allow_blank=True)


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
    bcc = EmailAddressSerializer(source="Bcc", many=True, required=False)
    body = serializers.CharField()
    # Format of the returned body (plain or html)
    body_format = serializers.CharField(source="mformat", required=False)
    date = serializers.CharField(source="Date")
    message_id = serializers.CharField(source="Message_ID", required=False)
    in_reply_to = serializers.CharField(source="In_Reply_To", required=False)
    references = serializers.CharField(source="References", required=False)
    # Reply-To may contain several addresses (parsed as a list)
    reply_to = EmailAddressSerializer(source="Reply_To", many=True, required=False)
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


class BaseEmailSerializer(serializers.Serializer):

    sender = serializers.EmailField()
    subject = serializers.CharField(required=False)
    body = serializers.CharField(required=False)
    to = serializers.ListField(child=serializers.EmailField(), required=False)
    cc = serializers.ListField(child=serializers.EmailField(), required=False)
    bcc = serializers.ListField(child=serializers.EmailField(), required=False)
    # Message this one replies to, kept in drafts
    in_reply_to = serializers.CharField(required=False)
    # References of the message this one replies to
    references = serializers.CharField(required=False)
    # Format chosen in the editor; the "editor" preference applies otherwise
    body_format = serializers.ChoiceField(
        choices=constants.DISPLAY_MODES, required=False
    )

    def validate_sender(self, value):
        """Ensure the sender is an address the user is allowed to use.

        Without this check a user could send with an arbitrary From address
        (identity spoofing).
        """
        user = self.context["request"].user
        if value.lower() not in allowed_sender_addresses(user):
            raise serializers.ValidationError(
                _("You are not allowed to send from this address")
            )
        return value

    def validate_to(self, value):
        return email_utils.prepare_addresses(value, "envelope")

    def validate_cc(self, value):
        return email_utils.prepare_addresses(value, "envelope")

    def validate_bcc(self, value):
        return email_utils.prepare_addresses(value, "envelope")


class SendEmailSerializer(ScheduledDatetimeMixin, BaseEmailSerializer):

    scheduled_datetime = serializers.DateTimeField(required=False)
    request_dsn = serializers.BooleanField(required=False, default=False)
    request_mdn = serializers.BooleanField(required=False, default=False)
    # UID of the draft this message comes from (deleted once sent)
    mailid = serializers.IntegerField(required=False)
    # Message this one replies to or forwards (flagged once sent)
    original_mailbox = serializers.CharField(required=False)
    original_mailid = serializers.IntegerField(required=False, min_value=1)
    original_action = serializers.ChoiceField(
        choices=["reply", "forward"], required=False
    )

    ORIGINAL_MESSAGE_FIELDS = ("original_mailbox", "original_mailid", "original_action")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["to"].required = True

    def validate(self, data):
        data = super().validate(data)
        if data.get("scheduled_datetime"):
            self.validate_scheduled_message_lengths(data)
        provided = [name for name in self.ORIGINAL_MESSAGE_FIELDS if name in data]
        if provided and len(provided) != len(self.ORIGINAL_MESSAGE_FIELDS):
            raise serializers.ValidationError(
                _(
                    "original_mailbox, original_mailid and original_action "
                    "must be provided together"
                )
            )
        return data

    def validate_scheduled_message_lengths(self, data):
        """Ensure a scheduled message fits in the database columns.

        A message sent right away has no such limit, but a scheduled one is
        stored first: a too long value would make the database fail.
        """
        errors = {}
        for name in ("subject", "in_reply_to"):
            max_length = models.ScheduledMessage._meta.get_field(name).max_length
            if len(data.get(name) or "") > max_length:
                errors[name] = _(
                    "Ensure this field has no more than %(max_length)s "
                    "characters to schedule the message"
                ) % {"max_length": max_length}
        if errors:
            raise serializers.ValidationError(errors)


class SaveEmailSerializer(BaseEmailSerializer):

    mailid = serializers.IntegerField(required=False)

    def create(self, validated_data):
        message = create_message(
            self.context["request"].user, validated_data, self.context["attachments"]
        )
        drafts_folder = self.context["request"].user.parameters.get_value(
            "drafts_folder"
        )
        mime_message = message.message()
        if validated_data.get("bcc"):
            # Django never writes Bcc into the MIME message: keep it in
            # the draft so it is not lost when the draft is reopened.
            mime_message["Bcc"] = ", ".join(validated_data["bcc"])
        with get_imapconnector(self.context["request"]) as imapc:
            if "mailid" in validated_data:
                imapc.delete_mail(drafts_folder, validated_data["mailid"])
            mailid = imapc.push_mail(drafts_folder, mime_message)
            imapc.mark_messages_unread(drafts_folder, [str(mailid)])
            return mailid


class ComposeSessionSerializer(serializers.Serializer):

    attachments = UploadedAttachmentSerializer(many=True, required=False)
    uid = serializers.CharField()
    signature = serializers.SerializerMethodField()
    editor_format = serializers.SerializerMethodField()

    def get_editor_format(self, obj):
        return self.context["request"].user.parameters.get_value("editor")

    def get_signature(self, obj):
        return str(signature.EmailSignature(self.context["request"].user))


class CreateSessionSerializer(serializers.Serializer):

    # Draft being edited: its attachments are copied into the session
    from_draft_message = serializers.IntegerField(required=False)
    # Message being forwarded: its attachments are copied too
    forward_mailbox = serializers.CharField(required=False)
    forward_mailid = serializers.IntegerField(required=False, min_value=1)

    def validate(self, data):
        data = super().validate(data)
        forward_fields = [
            name for name in ("forward_mailbox", "forward_mailid") if name in data
        ]
        if len(forward_fields) == 1:
            raise serializers.ValidationError(
                _("forward_mailbox and forward_mailid must be provided together")
            )
        if forward_fields and "from_draft_message" in data:
            raise serializers.ValidationError(
                _("A session can't start from a draft and a forwarded message")
            )
        return data


class AllowedSenderSerializer(serializers.Serializer):

    address = serializers.EmailField()


class ScheduledMessageSerializer(ScheduledDatetimeMixin, serializers.ModelSerializer):

    class Meta:
        model = models.ScheduledMessage
        fields = ["error", "scheduled_datetime"]
        read_only_fields = ["error"]

    def update(self, instance, validated_data):
        if instance.status == constants.SchedulingState.SEND_ERROR.value:
            # Rescheduling a failed message gives it another try
            instance.status = constants.SchedulingState.SCHEDULED.value
            instance.error = None
        instance = super().update(instance, validated_data)
        message = instance.to_email_message()
        with get_imapconnector(self.context["request"]) as imapc:
            if instance.imap_uid:
                # No IMAP copy (it failed, or the folder was cleaned up):
                # rescheduling must still work.
                imapc.delete_mail(constants.MAILBOX_NAME_SCHEDULED, instance.imap_uid)
            instance.imap_uid = imapc.push_mail(
                constants.MAILBOX_NAME_SCHEDULED, message.message()
            )
            instance.save()
        return instance
