"""PDF Credentials API v2 views."""

from django.http import HttpResponse

from rest_framework import permissions
from rest_framework.views import APIView

from modoboa.admin.models import Domain
from modoboa.lib.throttle import UserLesserDdosUser

from .serializers import GetAccountCredentialsSerializer

from ...lib import rfc_6266_content_disposition


class PDFCredentialView(APIView):

    permission_classes = (
        permissions.IsAuthenticated,
        permissions.DjangoModelPermissions,
    )

    serializer_class = GetAccountCredentialsSerializer
    throttle_classes = [UserLesserDdosUser]

    def get_queryset(self):
        """Filter queryset based on current user."""
        return Domain.objects.get_for_admin(self.request.user)

    def get(self, request, *args, **kwargs):
        """View to download a document."""
        data = {"account_id": kwargs["account_id"]}
        serializer = GetAccountCredentialsSerializer(
            data=data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        content = serializer.context["content"]
        fname = serializer.context["fname"]
        resp = HttpResponse(content)
        resp["Content-Type"] = "application/pdf"
        resp["Content-Length"] = len(content)
        resp["Content-Disposition"] = rfc_6266_content_disposition(fname)
        return resp
