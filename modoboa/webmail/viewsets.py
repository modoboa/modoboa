"""Webmail viewsets."""

from django.http import Http404, HttpResponse

from rest_framework import response, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from modoboa.lib.paginator import Paginator
from modoboa.webmail import lib, serializers


class UserMailboxViewSet(viewsets.GenericViewSet):
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.UserMailboxSerializer

    def list(self, request):
        parent_mailbox = request.GET.get("mailbox")
        imapc = lib.get_imapconnector(request)
        mboxes = imapc.getmboxes(request.user, parent_mailbox)
        serializer = serializers.UserMailboxSerializer(mboxes, many=True)
        return response.Response(serializer.data)


class UserEmailViewSet(viewsets.GenericViewSet):

    def get_serializer_class(self):
        if self.action == "list":
            return serializers.PaginatedEmailListSerializer
        if self.action in ["delete", "mark_as_junk", "mark_as_not_junk"]:
            return serializers.MoveSelectionSerializer
        if self.action == "flag":
            return serializers.FlagSelectionSerializer
        if self.action == "send":
            return serializers.SendEmailSerializer
        return serializers.EmailSerializer

    def list(self, request):
        mailbox = request.GET.get("mailbox", "INBOX")
        imapc = lib.get_imapconnector(request)
        total = imapc.messages_count(mbox=mailbox)
        messages_per_page = request.user.parameters.get_value("messages_per_page")
        paginator = Paginator(total, messages_per_page)
        page_num = int(request.GET.get("page", 1))
        page = paginator.getpage(int(request.GET.get("page", 1)))
        content = imapc.fetch(page.id_start, page.id_stop, mbox=mailbox)
        content = [dict(msg) for msg in content]
        serializer = serializers.EmailHeadersSerializer(content, many=True)
        return response.Response(
            {
                "count": total,
                "first_index": page_num * messages_per_page,
                "last_index": (page_num * messages_per_page) + len(content),
                "prev_page": page.previous_page_number if page.has_previous else None,
                "next_page": page.next_page_number if page.has_next else None,
                "results": serializer.data,
            }
        )

    def move_selection(self, request, destination: str) -> int:
        """Move selected messages to the given mailbox."""
        serializer = serializers.MoveSelectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        mbc = lib.get_imapconnector(request)
        mbc.move(
            ",".join(serializer.validated_data["selection"]),
            serializer.validated_data["mailbox"],
            destination,
        )
        return len(serializer.validated_data["selection"])

    @action(
        methods=["post"],
        detail=False,
        serializer_class=serializers.MoveSelectionSerializer,
    )
    def delete(self, request):
        count = self.move_selection(
            request, request.user.parameters.get_value("trash_folder")
        )
        return response.Response({"count": count})

    @action(
        methods=["post"],
        detail=False,
        serializer_class=serializers.MoveSelectionSerializer,
    )
    def mark_as_junk(self, request):
        count = self.move_selection(
            request, request.user.parameters.get_value("trash_folder")
        )
        return response.Response({"count": count})

    @action(
        methods=["post"],
        detail=False,
        serializer_class=serializers.MoveSelectionSerializer,
    )
    def mark_as_not_junk(self, request):
        count = self.move_selection(request, "INBOX")
        return response.Response({"count": count})

    @action(
        methods=["post"],
        detail=False,
        serializer_class=serializers.FlagSelectionSerializer,
    )
    def flag(self, request):
        serializer = serializers.FlagSelectionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        imapc = lib.get_imapconnector(request)
        getattr(imapc, f"mark_messages_{serializer.validated_data['status']}")(
            serializer.validated_data["mailbox"], serializer.validated_data["selection"]
        )
        return response.Response({"count": len(serializer.validated_data["selection"])})

    @action(methods=["get"], detail=False)
    def content(self, request):
        mailbox = request.GET.get("mailbox", "INBOX")
        mailid = request.GET.get("mailid")
        if not mailbox or not mailid:
            raise Http404
        dformat = request.user.parameters.get_value("displaymode")
        context = self.request.GET.get("context")
        if context and context in ["reply", "forward"]:
            modclass = getattr(lib, f"{context.capitalize()}Modifier")
            email = modclass(
                request,
                f"{mailbox}:{mailid}",
                dformat=dformat,
                links=request.GET.get("links", "0") == "1",
            )
        else:
            email = lib.ImapEmail(
                request,
                f"{mailbox}:{mailid}",
                dformat=dformat,
                links=request.GET.get("links", "0") == "1",
            )
            email.fetch_headers()
        serializer = serializers.EmailSerializer(email)
        return response.Response(serializer.data)

    @action(methods=["get"], detail=False)
    def source(self, request):
        mailbox = request.GET.get("mailbox", "INBOX")
        mailid = request.GET.get("mailid")
        if not mailbox or not mailid:
            raise Http404
        email = lib.ImapEmail(
            request,
            f"{mailbox}:{mailid}",
        )
        return response.Response({"source": email.source})

    @action(methods=["get"], detail=False)
    def attachment(self, request):
        mailbox = request.GET.get("mailbox", "INBOX")
        mailid = request.GET.get("mailid")
        partnum = request.GET.get("partnum")
        if not mailbox or not mailbox or not partnum:
            raise Http404
        imapc = lib.get_imapconnector(request)
        partdef, payload = imapc.fetchpart(mailid, mailbox, partnum)
        resp = HttpResponse(lib.decode_payload(partdef["encoding"], payload))
        resp["Content-Type"] = partdef["Content-Type"]
        resp["Content-Transfer-Encoding"] = partdef["encoding"]
        resp["Content-Disposition"] = lib.rfc6266.build_header("attachment")
        if int(partdef["size"]) < 200:
            resp["Content-Length"] = partdef["size"]
        return resp

    @action(methods=["post"], detail=False)
    def send(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        status, error = lib.send_mail(request, serializer.validated_data)
        if status:
            return response.Response(status=204)
        return response.Response({"error": error}, status=400)
