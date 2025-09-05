"""Amavis viewsets."""

from django.http import Http404
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext as _

import django_rq
from rest_framework import filters, mixins, permissions, response, viewsets
from rest_framework.decorators import action

from modoboa.amavis.sql_connector import SQLconnector
from modoboa.lib.paginator import Paginator
from modoboa.lib.permissions import CanViewDomain

from modoboa.admin import models as admin_models
from modoboa.amavis import models, serializers, tasks
from modoboa.amavis.lib import (
    AMrelease,
    manual_learning_enabled,
    SelfServiceAuthentication,
)
from modoboa.amavis.sql_email import SQLemail
from modoboa.amavis.utils import smart_str
from modoboa.parameters import tools as param_tools


SELFSERVICE_ACTIONS = ["retrieve", "headers", "delete", "release"]


def get_user_valid_addresses(user):
    """Retrieve all valid addresses of a user."""
    valid_addresses = []
    if user.role == "SimpleUsers":
        valid_addresses.append(user.email)
        try:
            mb = admin_models.Mailbox.objects.get(user=user)
        except admin_models.Mailbox.DoesNotExist:
            pass
        else:
            valid_addresses += mb.alias_addresses
    return valid_addresses


class QuarantineViewSet(viewsets.GenericViewSet):

    filter_backends = (filters.OrderingFilter,)
    ordering_fields = [
        "datetime",
        "from_address",
        "score",
        "subject",
        "to_address",
        "type",
    ]
    permission_classes = (permissions.IsAuthenticated,)

    def get_serializer_class(self):
        if self.action == "retrieve":
            return serializers.MessageSerializer
        if self.action == "headers":
            return serializers.MessageHeadersSerializer
        if self.action == "mark_selection":
            return serializers.MarkMessageSelectionSerializer
        if self.action in ["release_selection", "delete_selection"]:
            return serializers.MessageSelectionSerializer
        if self.action in ["delete", "release"]:
            return serializers.MessageIdentifierSerializer
        return serializers.PaginatedMessageListSerializer

    def get_authenticators(self):
        result = [auth() for auth in self.authentication_classes]
        if self.request:
            action = self.action_map.get(self.request.method.lower())
            if action in SELFSERVICE_ACTIONS:
                result = [SelfServiceAuthentication()] + result
        return result

    def get_permissions(self):
        if self.request.auth == "selfservice" and self.action in SELFSERVICE_ACTIONS:
            return []
        return super().get_permissions()

    def list(self, request):
        ordering = request.GET.get("ordering")
        connector = SQLconnector(user=request.user, ordering=ordering)
        try:
            page_size = int(request.GET.get("page_size"))
        except (TypeError, ValueError):
            page_size = request.user.parameters.get_value("messages_per_page")
        total = connector.messages_count(request)
        paginator = Paginator(total, page_size)
        page_num = int(request.GET.get("page", 1))
        page = paginator.getpage(page_num)
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
        email_list = connector.fetch(page.id_start, page.id_stop)
        serializer = self.get_serializer(
            {
                "count": total,
                "first_index": page_num * page_size,
                "last_index": (page_num * page_size) + len(email_list),
                "prev_page": page.previous_page_number if page.has_previous else None,
                "next_page": page.next_page_number if page.has_next else None,
                "results": email_list,
            }
        )
        return response.Response(serializer.data)

    def retrieve(self, request, pk):
        rcpt = request.GET.get("rcpt")
        if rcpt is None:
            return response.Response({"error": _("Invalid request")}, status=400)
        if request.user:
            if request.user.email == rcpt:
                SQLconnector().set_msgrcpt_status(rcpt, pk, "V")
            elif hasattr(request.user, "mailbox"):
                mb = request.user.mailbox
                if rcpt == mb.full_address or rcpt in mb.alias_addresses:
                    SQLconnector().set_msgrcpt_status(rcpt, pk, "V")
        mail = SQLemail(pk.encode("ascii"), dformat="plain")
        serializer = self.get_serializer(mail)
        return response.Response(serializer.data)

    @action(methods=["get"], detail=True)
    def headers(self, request, pk):
        email = SQLemail(pk.encode("ascii"))
        headers = []
        for name in email.msg.keys():
            headers.append({"name": name, "value": email.get_header(email.msg, name)})
        serializer = self.get_serializer({"headers": headers})
        return response.Response(serializer.data)

    def _release_selection(self, request, selection):
        connector = SQLconnector()
        valid_addresses = None
        if request.user:
            valid_addresses = get_user_valid_addresses(request.user)
        msgrcpts = []
        for item in selection:
            if valid_addresses and item["rcpt"] not in valid_addresses:
                continue
            msgrcpts += [
                (
                    item["mailid"],
                    connector.get_recipient_message(item["rcpt"], item["mailid"]),
                )
            ]
        if (
            not request.user or request.user.role == "SimpleUsers"
        ) and not param_tools.get_global_parameter("user_can_release"):
            for i, msgrcpt in msgrcpts:
                connector.set_msgrcpt_status(smart_str(msgrcpt.rid.email), i, "p")
            return response.Response({"status": "pending"})

        amr = AMrelease()
        error = None
        for mid, rcpt in msgrcpts:
            # we can't use the .mail relation on rcpt because it leads to
            # an error on Postgres (memoryview pickle error).
            mail = models.Msgs.objects.get(pk=mid.encode("ascii"))
            result = amr.sendreq(mid, mail.secret_id, rcpt.rid.email)
            if result:
                connector.set_msgrcpt_status(smart_str(rcpt.rid.email), mid, "R")
            else:
                error = result
                break

        if error:
            return response.Response({"status": error})

        return response.Response({"status": "released"})

    @action(methods=["post"], detail=False)
    def release_selection(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self._release_selection(request, serializer.validated_data["selection"])

    @action(methods=["post"], detail=True)
    def release(self, request, pk):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self._release_selection(request, [serializer.validated_data])

    def _delete_selection(self, request, selection):
        connector = SQLconnector()
        valid_addresses = None
        if request.user:
            valid_addresses = get_user_valid_addresses(request.user)
        for item in selection:
            if valid_addresses and item["rcpt"] not in valid_addresses:
                continue
            connector.set_msgrcpt_status(item["rcpt"], item["mailid"], "D")
        return response.Response(status=204)

    @action(methods=["post"], detail=False)
    def delete_selection(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self._delete_selection(request, serializer.validated_data["selection"])

    @action(methods=["post"], detail=True)
    def delete(self, request, pk):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return self._delete_selection(request, [serializer.validated_data])

    @action(methods=["post"], detail=False)
    def mark_selection(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        if not manual_learning_enabled(request.user):
            return response.Response({"status": "ok"})
        recipient_db = serializer.validated_data.get("database")
        if not recipient_db:
            recipient_db = "user" if request.user.role == "SimpleUsers" else "global"
        queue = django_rq.get_queue("modoboa")
        queue.enqueue(
            tasks.manual_learning,
            request.user.pk,
            serializer.validated_data["type"],
            serializer.validated_data["selection"],
            recipient_db,
        )
        return response.Response(status=204)


class PolicyViewSet(
    mixins.RetrieveModelMixin, mixins.UpdateModelMixin, viewsets.GenericViewSet
):

    permission_classes = (permissions.IsAuthenticated, CanViewDomain)
    serializer_class = serializers.PolicySerializer

    def get_queryset(self):
        domains = [
            f"@{name}"
            for name in admin_models.Domain.objects.get_for_admin(
                self.request.user
            ).values_list("name", flat=True)
        ]
        return models.Policy.objects.filter(users__email__in=domains)

    def get_object(self):
        """Return the object the view is displaying."""
        domain = get_object_or_404(admin_models.Domain, pk=self.kwargs["pk"])
        queryset = self.filter_queryset(self.get_queryset())
        obj = queryset.filter(users__email=f"@{domain.name}").first()
        if obj is None:
            raise Http404

        # May raise a permission denied
        self.check_object_permissions(self.request, obj)

        return obj
