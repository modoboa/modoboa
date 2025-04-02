"""Webmail serializers."""

from rest_framework import serializers

from modoboa.webmail import constants
from modoboa.webmail.lib import imapheader


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


class EmailAddressSerializer(serializers.Serializer):
    fulladdress = serializers.CharField()
    address = serializers.CharField()
    name = serializers.CharField(required=False)


class AttachmentSerializer(serializers.Serializer):
    name = serializers.CharField()
    partnum = serializers.CharField()


class EmailHeadersSerializer(serializers.Serializer):

    imapid = serializers.CharField()
    subject = serializers.SerializerMethodField()
    from_address = serializers.SerializerMethodField()
    date = serializers.SerializerMethodField()
    size = serializers.IntegerField()
    answered = serializers.BooleanField(default=False)
    attachments = serializers.BooleanField(default=False)
    forwarded = serializers.BooleanField(default=False)
    flagged = serializers.BooleanField(default=False)
    style = serializers.CharField(required=False)

    def get_subject(self, obj) -> str:
        return imapheader.parse_subject(obj["Subject"])

    def get_from_address(self, obj):
        return imapheader.parse_address(obj["From"])

    def get_date(self, obj) -> str:
        return imapheader.parse_date(obj["Date"])


class PaginatedEmailListSerializer(serializers.Serializer):

    count = serializers.IntegerField()
    first_index = serializers.IntegerField()
    last_index = serializers.IntegerField()
    prev_page = serializers.IntegerField()
    next_page = serializers.IntegerField()
    results = EmailHeadersSerializer(many=True)


class EmailSerializer(serializers.Serializer):

    subject = serializers.CharField(source="Subject")
    from_address = EmailAddressSerializer(source="From")
    to = EmailAddressSerializer(source="To", many=True)
    body = serializers.CharField()
    date = serializers.CharField(source="Date")
    attachments = serializers.SerializerMethodField()

    def get_attachments(self, email):
        result = []
        if email.attachments:
            for partnum, name in email.attachments.items():
                data = {"name": name, "partnum": partnum}
                result.append(data)
        return result


class MoveSelectionSerializer(serializers.Serializer):

    mailbox = serializers.CharField()
    selection = serializers.ListField(child=serializers.CharField())

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
