"""Viewsets for API V2 for imap_migration."""

import imaplib
import socket
import ssl

from rest_framework import response
from rest_framework.decorators import action

from modoboa.imap_migration.api.v1 import viewsets as v1_viewsets

from . import serializers


class EmailProviderViewSet(v1_viewsets.EmailProviderViewSet):

    @action(methods=["post"], detail=False)
    def check_connection(self, request, **kwargs):
        """check that provided information allow connection to imap server."""
        serializer = serializers.CheckProviderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        secured = serializer.data["secured"]
        address = serializer.data["address"]
        port = serializer.data["port"]
        try:
            if secured:
                imaplib.IMAP4_SSL(address, port)
            else:
                imaplib.IMAP4(address, port)
        except (socket.error, imaplib.IMAP4.error, ssl.SSLError) as error:
            return response.Response({'status': 'failed'}, 400)
        return response.Response(status=200)

    @action(methods=["post"], detail=False)
    def check_associated_domain(self, request, **kwargs):
        """check that the associated domain is either the same as the provider,
        or if a local domain already exists.
        This is to prevent errros on setup."""
        serializer = serializers.CheckAssociatedDomainSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return response.Response(status=200)


class MigrationViewSet(v1_viewsets.MigrationViewSet):
    """ Change the serializer to add the user id. """
    serializer_class = serializers.MigrationSerializer
