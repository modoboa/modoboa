"""DMARC models."""

from django.db import models
from django.utils.translation import gettext_lazy as _

from modoboa.admin import models as admin_models


POLICY_DISPOSITIONS = [
    ("none", _("None")),
    ("quarantine", _("Quarantine")),
    ("reject", _("Reject")),
]

COMMON_RESULTS = [
    ("none", _("None")),
    ("neutral", _("Neutral")),
    ("pass", _("Pass")),
    ("fail", _("Fail")),
    ("temperror", _("Temporary error")),
    ("permerror", _("Permanent error")),
]

DKIM_RESULTS = COMMON_RESULTS + [("policy", _("Policy"))]

SPF_RESULTS = COMMON_RESULTS + [("softfail", _("Soft failure"))]

RECORD_TYPES = [
    ("dkim", "DKIM"),
    ("spf", "SPF"),
]


class Reporter(models.Model):
    """Report issuers."""

    org_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)

    def __str__(self):
        """Return name and email."""
        return f"{self.org_name} <{self.email}>"


class Report(models.Model):
    """Aggregated reports."""

    report_id = models.CharField(max_length=100)
    reporter = models.ForeignKey(Reporter, on_delete=models.CASCADE)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()

    # Published policy
    policy_domain = models.CharField(max_length=100)
    policy_adkim = models.CharField(max_length=1)
    policy_aspf = models.CharField(max_length=1)
    policy_p = models.CharField(max_length=10)
    policy_sp = models.CharField(max_length=10)
    policy_pct = models.SmallIntegerField()

    class Meta:
        unique_together = ("reporter", "report_id")

    def __str__(self):
        """Display provider and dates."""
        return f"{self.reporter}: {self.start_date} -> {self.end_date}"


class Record(models.Model):
    """Report records."""

    report = models.ForeignKey(Report, on_delete=models.CASCADE)
    source_ip = models.GenericIPAddressField()
    count = models.IntegerField()

    # Policy evaluated
    disposition = models.CharField(max_length=10, choices=POLICY_DISPOSITIONS)
    dkim_result = models.CharField(max_length=9, choices=DKIM_RESULTS)
    spf_result = models.CharField(max_length=9, choices=SPF_RESULTS)
    header_from = models.ForeignKey(admin_models.Domain, on_delete=models.CASCADE)
    reason_type = models.CharField(max_length=15, blank=True)
    reason_comment = models.CharField(max_length=100, blank=True)


class Result(models.Model):
    """Record results."""

    record = models.ForeignKey(Record, on_delete=models.CASCADE)
    type = models.CharField(max_length=4, choices=RECORD_TYPES)
    domain = models.CharField(max_length=100)
    result = models.CharField(max_length=9)
