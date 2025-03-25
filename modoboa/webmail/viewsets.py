"""Webmail viewsets."""

from django.http import Http404

from rest_framework import response, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from modoboa.lib.paginator import Paginator
from modoboa.webmail import lib, serializers


class UserMailboxViewSet(viewsets.GenericViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.UserMailboxSerializer

    def list(self, request):
        parent_mailbox = request.GET.get("mailbox", "")
        imapc = lib.get_imapconnector(request)
        mboxes = imapc.getmboxes(request.user, parent_mailbox)
        serializer = serializers.UserMailboxSerializer(mboxes, many=True)
        return response.Response(serializer.data)


class UserEmailViewSet(viewsets.GenericViewSet):

    def list(self, request):
        mailbox = request.GET.get("mailbox", "INBOX")
        imapc = lib.get_imapconnector(request)
        paginator = Paginator(
            imapc.messages_count(mbox=mailbox),
            request.user.parameters.get_value("messages_per_page"),
        )
        page = paginator.getpage(1)
        content = imapc.fetch(page.id_start, page.id_stop, mbox=mailbox)
        content = [dict(msg) for msg in content]
        serializer = serializers.EmailHeadersSerializer(content, many=True)
        return response.Response(serializer.data)

    @action(methods=["get"], detail=False)
    def content(self, request):
        mailbox = request.GET.get("mailbox", "INBOX")
        mailid = request.GET.get("mailid")
        if not mailbox or not mailid:
            raise Http404
        email = lib.ImapEmail(request, f"{mailbox}:{mailid}")
        email.fetch_headers()
        serializer = serializers.EmailSerializer(email)
        return response.Response(serializer.data)
