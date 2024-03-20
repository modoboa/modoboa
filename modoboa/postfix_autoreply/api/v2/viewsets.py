"""Autoreply viewsets."""

from django_filters import rest_framework as filters
from drf_spectacular.utils import extend_schema
from rest_framework import mixins, permissions, response, viewsets
from rest_framework.decorators import action

from modoboa.admin import models as admin_models
from modoboa.lib.email_utils import split_mailbox
from modoboa.parameters import tools as param_tools

from modoboa.postfix_autoreply import models
from . import serializers


class ARMessageFilterSet(filters.FilterSet):
    """Filter set for ARmessage."""

    mbox = filters.CharFilter(method="filter_mbox")

    class Meta:
        fields = ("mbox", "mbox__user")
        model = models.ARmessage

    def filter_mbox(self, queryset, name, value):
        address, domain = split_mailbox(value)
        if address:
            queryset = queryset.filter(mbox__address__icontains=address)
        if domain:
            queryset = queryset.filter(mbox__domain__name__icontains=domain)
        return queryset


class ARMessageViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    """A viewset for ARmessage."""

    filter_backends = (filters.DjangoFilterBackend,)
    filterset_class = ARMessageFilterSet
    permission_classes = (permissions.IsAuthenticated,)
    queryset = models.ARmessage.objects.select_related("mbox__domain", "mbox__user")
    serializer_class = serializers.ARMessageSerializer

    def get_queryset(self):
        """Filter queryset based on current user."""
        qset = super().get_queryset()
        role = self.request.user.role
        if role == "SimpleUsers":
            qset = qset.filter(mbox=self.request.user.mailbox)
        elif role in ["DomainAdmins", "Resellers"]:
            mailboxes = admin_models.Mailbox.objects.get_for_admin(self.request.user)
            qset = qset.filter(mbox__in=mailboxes)
        return qset


class AccountARMessageViewSet(viewsets.ViewSet):
    """A viewset dedicated to connected account."""

    permission_classes = (permissions.IsAuthenticated,)
    serializer_class = serializers.AccountARMessageSerializer

    @extend_schema(
        description="Get current auto-reply message",
        methods=["GET"],
    )
    @extend_schema(
        description="Set auto-reply message",
        methods=["PUT"],
    )
    @action(methods=["get", "put"], detail=False)
    def armessage(self, request):
        if not hasattr(request.user, "mailbox"):
            return response.Response(status=404)
        params = dict(param_tools.get_global_parameters("postfix_autoreply"))
        armessage, created = models.ARmessage.objects.get_or_create(
            mbox=self.request.user.mailbox,
            defaults={
                "subject": params["default_subject"],
                "content": params["default_content"],
            },
        )
        if request.method == "GET":
            serializer = serializers.AccountARMessageSerializer(armessage)
            return response.Response(serializer.data)
        serializer = serializers.AccountARMessageSerializer(
            armessage, data=request.data
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return response.Response(serializer.validated_data)
