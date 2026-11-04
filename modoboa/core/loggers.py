import logging

from django.core.exceptions import ObjectDoesNotExist


class SQLHandler(logging.Handler):

    def emit(self, record):
        from .models import Log

        Log.objects.create(
            message=record.getMessage(),
            level=record.levelname,
            logger=record.name,
            **getattr(record, "audit", {}),
        )


def get_domain_name(obj) -> str:
    """Return the name of the mail domain an object belongs to, if any."""
    label = obj._meta.label
    if label == "admin.Domain":
        return obj.name
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
    **extra,
) -> dict:
    """Build the `extra` argument that turns a log call into an audit entry.

    Usage: logger.info(msg, extra=audit("core.login.succeeded", request))
    """
    if request is not None:
        if actor is None and request.user.is_authenticated:
            actor = request.user
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
        data["domain"] = get_domain_name(obj)
    return {"audit": data}
