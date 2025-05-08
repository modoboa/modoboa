"""Custom SMTP email backend."""

from django.core.mail.backends import EmailBackend
from django.core.mail.utils import DNS_NAME

from modoboa.lib import oauth2


class OAuthBearerEmailBackend(EmailBackend):

    def open(self):
        """
        Ensure an open connection to the email server. Return whether or not a
        new connection was required (True or False) or None if an exception
        passed silently.
        """
        if self.connection:
            # Nothing to do if the connection is already open.
            return False

        # If local_hostname is not specified, socket.getfqdn() gets used.
        # For performance, we use the cached FQDN for local_hostname.
        connection_params = {"local_hostname": DNS_NAME.get_fqdn()}
        if self.timeout is not None:
            connection_params["timeout"] = self.timeout
        if self.use_ssl:
            connection_params["context"] = self.ssl_context
        try:
            self.connection = self.connection_class(
                self.host, self.port, **connection_params
            )

            # TLS/SSL are mutually exclusive, so only attempt TLS over
            # non-secure connections.
            if not self.use_ssl and self.use_tls:
                self.connection.starttls(context=self.ssl_context)
            if self.username and self.password:
                token = oauth2.build_oauthbearer_string(self.username, self.password)
                self.connection.docmd("AUTH", f"OAUTHBEARER {token.decode('utf-8')}")
            return True
        except OSError:
            if not self.fail_silently:
                raise
