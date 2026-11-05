import logging

from django.core.exceptions import ObjectDoesNotExist
from django.utils.text import capfirst
from django.utils.translation import gettext as _, gettext_lazy

_AUDIT_ACTIONS = {}


def register_audit_action(code: str, label) -> None:
    """Declare an audit action code and its (lazy) label.

    Extensions call it from their AppConfig.ready().
    """
    _AUDIT_ACTIONS[code] = label


def get_audit_actions() -> dict[str, str]:
    """Return every known audit action code with its label.

    Models tracked by reversion get <app>.<model>.created|modified|deleted.
    """
    from reversion import revisions as reversion

    verbs = {
        "created": _("%(model)s created"),
        "modified": _("%(model)s modified"),
        "deleted": _("%(model)s deleted"),
    }
    actions = {}
    for model in reversion.get_registered_models():
        name = capfirst(model._meta.verbose_name)
        for verb, label in verbs.items():
            code = f"{model._meta.app_label}.{model._meta.model_name}.{verb}"
            actions[code] = label % {"model": name}
    actions.update({code: str(label) for code, label in _AUDIT_ACTIONS.items()})
    return actions


for _code, _label in (
    ("core.login.succeeded", gettext_lazy("Login succeeded")),
    ("core.login.failed", gettext_lazy("Login failed")),
    ("core.login.tfa_failed", gettext_lazy("Two-factor authentication failed")),
    (
        "core.tfa_settings.password_failed",
        gettext_lazy("Wrong password while editing 2FA settings"),
    ),
    ("core.password.changed", gettext_lazy("Password changed")),
    ("core.password.reset_requested", gettext_lazy("Password reset requested")),
    ("core.password.reset", gettext_lazy("Password reset")),
    ("core.tfa.totp_enabled", gettext_lazy("Authenticator app enabled")),
    ("core.tfa.totp_disabled", gettext_lazy("Authenticator app disabled")),
    ("core.tfa.recovery_codes_reset", gettext_lazy("Recovery codes regenerated")),
    ("core.tfa.fido_key_added", gettext_lazy("Security key added")),
    ("core.tfa.fido_key_removed", gettext_lazy("Security key removed")),
    ("core.api_token.created", gettext_lazy("API token created")),
    ("core.api_token.deleted", gettext_lazy("API token deleted")),
    ("core.parameters.modified", gettext_lazy("Global parameters modified")),
):
    register_audit_action(_code, _label)


class SQLHandler(logging.Handler):

    def emit(self, record):
        from . import signals
        from .models import Log

        audit_data = getattr(record, "audit", {})
        log = Log.objects.create(
            message=record.getMessage(),
            level=record.levelname,
            logger=record.name,
            **audit_data,
        )
        if not audit_data:
            return
        # A failing receiver must not break the audited operation
        for receiver, result in signals.audit_event_created.send_robust(
            sender=Log, log=log
        ):
            if isinstance(result, Exception):
                logging.getLogger("modoboa.audit").error(
                    "audit_event_created receiver %s failed",
                    receiver,
                    exc_info=result,
                )


def get_domain_name(obj) -> str:
    """Return the name of the mail domain an object belongs to, if any."""
    label = obj._meta.label
    if label == "admin.Domain":
        return obj.name
    if label == "core.User" and obj.is_superuser:
        # A super admin owning a mailbox must not expose its activity
        # (logins, API tokens...) to the administrators of that domain
        return ""
    # Related rows may already be gone when logging a cascade deletion
    try:
        if label in ("core.User", "admin.SenderAddress"):
            obj = getattr(obj, "mailbox", None)
        domain = getattr(obj, "domain", None) or getattr(obj, "target", None)
    except ObjectDoesNotExist:
        return ""
    return domain.name if domain else ""


def audit(
    action: str,
    request=None,
    *,
    actor=None,
    actor_name: str = "",
    ip: str | None = None,
    obj=None,
    domain: str = "",
    **extra,
) -> dict:
    """Build the `extra` argument that turns a log call into an audit entry.

    Usage: logger.info(msg, extra=audit("core.login.succeeded", request))
    The action code must be declared with register_audit_action().

    The domain decides which domain administrators see the entry: it
    comes from the object, else from the actor's mailbox, unless given.
    """
    if request is not None:
        # No user on some self-service requests (quarantine links)
        user = getattr(request, "user", None)
        if actor is None and user is not None and user.is_authenticated:
            actor = user
        ip = ip or request.META.get("REMOTE_ADDR")
    data = {"action": action, "ip_address": ip, "extra": extra}
    if actor is not None:
        data["actor"] = actor
        data["actor_name"] = actor.username
    else:
        # May be user input (failed login): fit the column
        data["actor_name"] = actor_name[:254]
    if obj is not None:
        from django.contrib.contenttypes.models import ContentType

        data["content_type"] = ContentType.objects.get_for_model(obj)
        data["object_id"] = obj.pk
        data["object_repr"] = str(obj)[:255]
        domain = get_domain_name(obj)
    elif not domain and actor is not None:
        domain = get_domain_name(actor)
    # May come from user input (failed login): fit the column
    data["domain"] = domain[:253]
    return {"audit": data}
