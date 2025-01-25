"""Contacts constants."""

from django.utils.translation import gettext_lazy

EMAIL_TYPES = (
    ("home", gettext_lazy("Home")),
    ("work", gettext_lazy("Work")),
    ("other", gettext_lazy("Other")),
)

PHONE_TYPES = (
    ("home", gettext_lazy("Home")),
    ("work", gettext_lazy("Work")),
    ("other", gettext_lazy("Other")),
    ("main", gettext_lazy("Main")),
    ("cell", gettext_lazy("Cellular")),
    ("fax", gettext_lazy("Fax")),
    ("pager", gettext_lazy("Pager")),
)

CDAV_TO_MODEL_FIELDS_MAP = {
    "org": "company",
    "title": "position",
    "note": "note",
}
