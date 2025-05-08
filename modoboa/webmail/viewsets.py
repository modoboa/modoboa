"""Webmail viewsets."""

from django import forms
from django.core.validators import validate_email
from django.http import Http404, HttpResponse
from django.utils.translation import gettext as _

from rest_framework import parsers, response, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from modoboa.lib.paginator import Paginator
from modoboa.lib.viewsets import HasMailbox
from modoboa.webmail import lib, serializers
from modoboa.webmail.lib import attachments


class UserMailboxViewSet(viewsets.GenericViewSet):

    permission_classes = (IsAuthenticated, HasMailbox)

    def get_serializer_class(self):
        if self.action == "quota":
            return serializers.UserMailboxQuotaSerializer
        if self.action == "unseen":
            return serializers.UserMailboxUnseenSerializer
        if self.action in ["create", "compress", "empty", "delete"]:
            return serializers.UserMailboxInputSerializer
        if self.action == "rename":
            return serializers.UserMailboxUpdateSerializer
        return serializers.UserMailboxesSerializer

    def list(self, request):
        parent_mailbox = request.GET.get("mailbox")
        with lib.get_imapconnector(request) as imapc:
            mboxes = imapc.getmboxes(request.user, parent_mailbox)
        serializer = self.get_serializer(
            {"mailboxes": mboxes, "hdelimiter": imapc.hdelimiter}
        )
        return response.Response(serializer.data)

    @action(methods=["get"], detail=False)
    def quota(self, request):
        mailbox = request.GET.get("mailbox")
        if mailbox is None:
            raise Http404
        with lib.get_imapconnector(request) as imapc:
            imapc.getquota(mailbox)
            serializer = self.get_serializer(imapc)
        return response.Response(serializer.data)

    @action(methods=["get"], detail=False)
    def unseen(self, request):
        """Get unseen messages counter for given mailbox."""
        mailbox = request.GET.get("mailbox")
        if mailbox is None:
            raise Http404
        with lib.get_imapconnector(request) as imapc:
            serializer = self.get_serializer(
                {"counter": imapc.unseen_messages(mailbox)}
            )
        return response.Response(serializer.data)

    def create(self, request):
        serializer = serializers.UserMailboxInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with lib.get_imapconnector(request) as imapc:
            imapc.create_folder(
                serializer.validated_data["name"],
                serializer.validated_data.get("parent_mailbox"),
            )
        return response.Response(serializer.validated_data, status=201)

    @action(methods=["post"], detail=False)
    def rename(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with lib.get_imapconnector(request) as imapc:
            oldname, oldparent = lib.separate_mailbox(
                serializer.validated_data["oldname"], sep=imapc.hdelimiter
            )
            name = serializer.validated_data["name"]
            parent = serializer.validated_data.get("parent_mailbox")
            if name != oldname or parent != oldparent:
                newname = (
                    name if parent is None else imapc.hdelimiter.join([parent, name])
                )
                imapc.rename_folder(oldname, newname)
        return response.Response(serializer.validated_data)

    @action(methods=["post"], detail=False)
    def compress(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with lib.get_imapconnector(request) as imapc:
            imapc.compact(serializer.validated_data["name"])
        return response.Response(status=204)

    @action(methods=["post"], detail=False)
    def empty(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        mailbox = serializer.validated_data["name"]
        if mailbox != request.user.parameters.get_value("trash_folder"):
            raise Http404
        with lib.get_imapconnector(request) as imapc:
            imapc.empty(mailbox)
        return response.Response(status=204)

    @action(methods=["post"], detail=False)
    def delete(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with lib.get_imapconnector(request) as imapc:
            imapc.delete_folder(serializer.validated_data["name"])
        return response.Response(status=204)


class UserEmailViewSet(viewsets.GenericViewSet):

    permission_classes = (IsAuthenticated, HasMailbox)

    def get_serializer_class(self):
        if self.action == "list":
            return serializers.PaginatedEmailListSerializer
        if self.action in ["delete", "mark_as_junk", "mark_as_not_junk"]:
            return serializers.MoveSelectionSerializer
        if self.action == "flag":
            return serializers.FlagSelectionSerializer
        return serializers.EmailSerializer

    def list(self, request):
        mailbox = request.GET.get("mailbox", "INBOX")
        search = request.GET.get("search")
        with lib.get_imapconnector(request) as imapc:
            if search:
                imapc.parse_search_parameters("both", search)
            total = imapc.messages_count(mbox=mailbox)
            messages_per_page = request.user.parameters.get_value("messages_per_page")
            paginator = Paginator(total, messages_per_page)
            page_num = int(request.GET.get("page", 1))
            page = paginator.getpage(int(request.GET.get("page", 1)))
            if not page:
                serializer = self.get_serializer(
                    {
                        "count": 0,
                        "first_index": 0,
                        "last_index": 0,
                        "prev_page": None,
                        "next_page": None,
                        "results": [],
                    }
                )
                return response.Response(serializer.data)

            content = imapc.fetch(page.id_start, page.id_stop, mbox=mailbox)
        content = [dict(msg) for msg in content]
        serializer = self.get_serializer(
            {
                "count": total,
                "first_index": page_num * messages_per_page,
                "last_index": (page_num * messages_per_page) + len(content),
                "prev_page": page.previous_page_number if page.has_previous else None,
                "next_page": page.next_page_number if page.has_next else None,
                "results": content,
            }
        )
        return response.Response(serializer.data)

    def move_selection(self, request, destination: str) -> int:
        """Move selected messages to the given mailbox."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with lib.get_imapconnector(request) as mbc:
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
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        with lib.get_imapconnector(request) as imapc:
            getattr(imapc, f"mark_messages_{serializer.validated_data['status']}")(
                serializer.validated_data["mailbox"],
                serializer.validated_data["selection"],
            )
        return response.Response({"count": len(serializer.validated_data["selection"])})

    @action(methods=["get"], detail=False)
    def content(self, request):
        mailbox = request.GET.get("mailbox", "INBOX")
        mailid = request.GET.get("mailid")
        if not mailbox or not mailid:
            raise Http404
        dformat = request.user.parameters.get_value("displaymode")
        if "dformat" in request.GET:
            dformat = request.GET.get("dformat")
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
        with lib.get_imapconnector(request) as imapc:
            partdef, payload = imapc.fetchpart(mailid, mailbox, partnum)
        resp = HttpResponse(lib.decode_payload(partdef["encoding"], payload))
        resp["Content-Type"] = partdef["Content-Type"]
        resp["Content-Transfer-Encoding"] = partdef["encoding"]
        resp["Content-Disposition"] = lib.rfc6266.build_header("attachment")
        if int(partdef["size"]) < 200:
            resp["Content-Length"] = partdef["size"]
        return resp


class ComposeSessionViewSet(viewsets.GenericViewSet):

    permission_classes = (IsAuthenticated, HasMailbox)

    def initialize_request(self, request, *args, **kwargs):
        response = super().initialize_request(request, *args, **kwargs)
        if self.action == "attachments":
            uploader = attachments.AttachmentUploadHandler()
            request.upload_handlers.insert(0, uploader)
        return response

    def get_serializer_class(self):
        if self.action == "send":
            return serializers.SendEmailSerializer
        if self.action == "allowed_senders":
            return serializers.AllowedSenderSerializer
        return serializers.ComposeSessionSerializer

    def retrieve(self, request, pk=None):
        manager = attachments.ComposeSessionManager(request.user.username)
        session = manager.get_content(pk)
        serializer = self.get_serializer(
            {"uid": pk, "attachments": session["attachments"]}
        )
        return response.Response(serializer.data)

    def create(self, request):
        uid = attachments.ComposeSessionManager(request.user.username).create()
        serializer = self.get_serializer({"uid": uid})
        return response.Response(serializer.data, status=201)

    @action(methods=["get"], detail=False)
    def allowed_senders(self, request):
        addresses = [{"address": request.user.email}]
        for address in request.user.mailbox.alias_addresses:
            try:
                validate_email(address)
                addresses.append({"address": address})
            except forms.ValidationError:
                pass
        addresses += [
            {"address": address}
            for address in request.user.mailbox.senderaddress_set.values_list(
                "address", flat=True
            )
        ]
        serializer = self.get_serializer(addresses, many=True)
        return response.Response(serializer.data)

    @action(methods=["post"], detail=True, parser_classes=(parsers.MultiPartParser,))
    def attachments(self, request, pk):
        serializer = serializers.AttachmentUploadSerializer(data=request.FILES)
        if not serializer.is_valid():
            errors = serializer.errors
            if request.upload_handlers[0].toobig:
                errors["attachment"] = [
                    _("Attachment is too big (limit: %s)")
                    % request.upload_handlers[0].maxsize
                ]
                return response.Response(errors, status=400)
        result = attachments.save_attachment(
            request, pk, serializer.validated_data["attachment"]
        )
        return response.Response(result)

    @action(methods=["delete"], detail=True, url_path="attachments/(?P<name>[^/.]+)")
    def delete_attachment(self, request, pk, name):
        error = attachments.remove_attachment(request, pk, name)
        if error:
            return response.Response({"error": error}, status=400)
        return response.Response(status=204)

    @action(methods=["post"], detail=True)
    def send(self, request, pk):
        """Send an email based on the given compose session."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        manager = attachments.ComposeSessionManager(request.user.username)
        status, error = lib.send_mail(
            request, serializer.validated_data, manager.get_content(pk)["attachments"]
        )
        if status:
            attachments.remove_attachments_and_session(manager, pk)
            return response.Response(status=204)
        return response.Response({"error": error}, status=400)
