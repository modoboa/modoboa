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


class EmailHeadersSerializer(serializers.Serializer):

    mailid = serializers.CharField()
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


class EmailSerializer(serializers.Serializer):

    subject = serializers.CharField(source="Subject")
    from_address = EmailAddressSerializer(source="From")
    body = serializers.CharField()
