"""Modoboa core viewsets."""

from django.http import Http404

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from . import models
from . import serializers


class UserPasswordChangeAPIView(APIView):

    """A view to update password for user instances."""

    def put(self, request, pk, format=None):
        """PUT method hander."""
        try:
            user = models.User.objects.get(username=pk)
        except models.User.DoesNotExist:
            raise Http404
        serializer = serializers.UserPasswordSerializer(
            user, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response()
        return Response(
            serializer.errors, status=status.HTTP_400_BAD_REQUEST)
