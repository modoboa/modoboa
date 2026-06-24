"""Internal library."""

import concurrent.futures
import datetime
import email
import fileinput
import getpass
import imaplib
import zipfile
import gzip
import sys
import tldextract

from defusedxml.ElementTree import fromstring
from dns import resolver, reversename
import magic
import io

from django.conf import settings
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.utils.encoding import smart_str
from django.utils.translation import gettext as _

from modoboa.admin import models as admin_models
from modoboa.parameters import tools as param_tools

from . import constants
from . import models

ZIP_CONTENT_TYPES = [
    "application/x-zip-compressed",
    "application/x-zip",
    "application/zip",
    "application/gzip",
    "application/octet-stream",
    "text/xml",
]

FILE_TYPES = [
    "text/plain",
    "text/xml",
]

# Size bounds to protect the importer against decompression bombs
# (CWE-409/CWE-400). Defaults live in the project settings so they can be
# tuned per deployment; DMARC aggregate reports are small in practice, so
# these caps are generous while still preventing resource exhaustion.
MAX_COMPRESSED_SIZE = getattr(
    settings, "DMARC_MAX_COMPRESSED_SIZE", 1 * 1024 * 1024
)  # 1 MiB of compressed attachment
MAX_DECOMPRESSED_SIZE = getattr(
    settings, "DMARC_MAX_DECOMPRESSED_SIZE", 20 * 1024 * 1024
)  # 20 MiB once decompressed
MAX_ZIP_MEMBERS = getattr(
    settings, "DMARC_MAX_ZIP_MEMBERS", 20
)  # number of files allowed inside a zip archive


def _read_bounded(fileobj, limit):
    """Read at most ``limit`` bytes and reject anything larger.

    Reading ``limit + 1`` bytes lets us detect oversized payloads
    without materializing the whole (potentially huge) stream.
    """
    data = fileobj.read(limit + 1)
    if len(data) > limit:
        raise ValueError("Decompressed payload exceeds the allowed size")
    return data


def import_record(xml_node, report):
    """Import a record."""
    record = models.Record(report=report)
    row = xml_node.find("row")
    record.source_ip = row.find("source_ip").text
    record.count = int(row.find("count").text)

    policy_evaluated = row.find("policy_evaluated")
    record.disposition = policy_evaluated.find("disposition").text
    record.dkim_result = policy_evaluated.find("dkim").text
    record.spf_result = policy_evaluated.find("spf").text
    reason = policy_evaluated.find("reason")
    if reason:
        record.reason_type = smart_str(reason.find("type").text)[:14]
        if record.reason_type not in constants.ALLOWED_REASON_TYPES:
            record.reason_type = "other"
        comment = reason.find("comment").text or ""
        record.reason_comment = comment

    identifiers = xml_node.find("identifiers")
    header_from = identifiers.find("header_from").text.split(".")
    domain = None
    while len(header_from) >= 2:
        domain = admin_models.Domain.objects.filter(name=".".join(header_from)).first()
        if domain is not None:
            record.header_from = domain
            break
        header_from = header_from[1:]
    if domain is None:
        print("Invalid record found (domain not local)")
        return None

    record.save()
    auth_results = xml_node.find("auth_results")
    for rtype in ["spf", "dkim"]:
        rnode = auth_results.find(rtype)
        if not rnode:
            continue
        domain = (rnode.findtext("domain") or "").strip()
        if not domain:
            domain = record.header_from.name
        result = (rnode.findtext("result") or "").strip()
        models.Result.objects.create(
            record=record,
            type=rtype,
            domain=domain,
            result=result,
        )


@transaction.atomic
def import_report(content):
    """Import an aggregated report."""
    root = fromstring(content, forbid_dtd=True)
    metadata = root.find("report_metadata")
    print(
        "Importing report {} received from {}".format(
            metadata.find("report_id").text, metadata.find("org_name").text
        )
    )
    reporter, created = models.Reporter.objects.get_or_create(
        email=metadata.find("email").text or "-",
        defaults={"org_name": metadata.find("org_name").text},
    )
    qs = models.Report.objects.filter(
        reporter=reporter, report_id=metadata.find("report_id").text
    )
    if qs.exists():
        print("Report already imported.")
        return
    report = models.Report(reporter=reporter)

    report.report_id = metadata.find("report_id").text
    date_range = metadata.find("date_range")
    report.start_date = timezone.make_aware(
        datetime.datetime.fromtimestamp(int(date_range.find("begin").text))
    )
    report.end_date = timezone.make_aware(
        datetime.datetime.fromtimestamp(int(date_range.find("end").text))
    )

    policy_published = root.find("policy_published")
    for attr in ["domain", "adkim", "aspf", "p", "sp", "pct"]:
        node = policy_published.find(attr)
        if node is None or not node.text:
            if attr == "sp":
                node = fromstring("<sp>unstated</sp>", forbid_dtd=True)
            else:
                print(f"Report skipped because of malformed data (empty {attr})")
                return
        setattr(report, f"policy_{attr}", node.text)
    report.save()
    for record in root.findall("record"):
        import_record(record, report)


def import_archive(archive, content_type=None):
    """Import reports contained inside (file pointer)
    - a zip archive,
    - a gzip file,
    - a xml file.
    """
    if content_type == "text/xml":
        import_report(_read_bounded(archive, MAX_DECOMPRESSED_SIZE))
    elif content_type in ["application/gzip", "application/octet-stream"]:
        with gzip.GzipFile(mode="r", fileobj=archive) as zfile:
            import_report(_read_bounded(zfile, MAX_DECOMPRESSED_SIZE))
    else:
        with zipfile.ZipFile(archive, "r") as zfile:
            infos = zfile.infolist()
            if len(infos) > MAX_ZIP_MEMBERS:
                raise ValueError("Too many members in zip archive")
            total = 0
            for info in infos:
                total += info.file_size
                if (
                    info.file_size > MAX_DECOMPRESSED_SIZE
                    or total > MAX_DECOMPRESSED_SIZE
                ):
                    raise ValueError("Decompressed payload exceeds the allowed size")
            for info in infos:
                with zfile.open(info, "r") as member:
                    # Enforce the cap on the real stream too: the declared
                    # file_size above cannot be fully trusted.
                    import_report(_read_bounded(member, MAX_DECOMPRESSED_SIZE))


def import_report_from_email(content):
    """Import a report from an email."""
    if isinstance(content, str):
        msg = email.message_from_string(content)
    elif isinstance(content, bytes):
        msg = email.message_from_bytes(content)
    else:
        msg = email.message_from_file(content)
    err = False
    for part in msg.walk():
        if part.get_content_type() not in ZIP_CONTENT_TYPES:
            continue
        try:
            payload = part.get_payload(decode=True)
            if payload is None:
                continue
            if len(payload) > MAX_COMPRESSED_SIZE:
                raise ValueError("Compressed attachment exceeds the allowed size")
            fpo = io.BytesIO(payload)
            # Try to get the actual file type of the buffer
            # required to make sure we are dealing with an XML file
            file_type = magic.Magic(uncompress=True, mime=True).from_buffer(
                fpo.read(2048)
            )
            fpo.seek(0)
            if file_type in FILE_TYPES:
                import_archive(fpo, content_type=part.get_content_type())
        except (OSError, ValueError, zipfile.BadZipFile):
            print("Error: the attachment does not match the mimetype")
            err = True
        else:
            fpo.close()
    if err:
        # Return EX_DATAERR code <data format error> available
        # at sysexits.h file
        # (see http://www.postfix.org/pipe.8.html)
        sys.exit(65)


def import_report_from_stdin():
    """Parse a report from stdin."""
    content = io.StringIO()
    for line in fileinput.input([]):
        content.write(line)
    content.seek(0)

    if not content:
        return
    import_report_from_email(content)


def import_from_imap(options):
    """Import reports from an IMAP mailbox."""
    obj = imaplib.IMAP4_SSL if options["ssl"] else imaplib.IMAP4
    conn = obj(options["host"])
    username = input("Username: ")
    password = getpass.getpass(prompt="Password: ")
    conn.login(username, password)
    conn.select(options["mailbox"])
    type, msg_ids = conn.search(None, "ALL")
    for msg_id in msg_ids[0].split():
        typ, content = conn.fetch(msg_id, "(RFC822)")
        for response_part in content:
            if isinstance(response_part, tuple):
                import_report_from_email(response_part[1])
    conn.close()


def week_range(year, weeknumber):
    """Return start and end dates of a given week."""
    tz = timezone.get_current_timezone()
    fmt = "%G-%V-%w"
    start_week = datetime.datetime.strptime(f"{year}-{weeknumber}-{1}", fmt)
    end_week = datetime.datetime.strptime(f"{year}-{weeknumber}-{0}", fmt)
    return start_week.replace(tzinfo=tz), end_week.replace(tzinfo=tz)


def insert_record(target: dict, record, name: str) -> None:
    """Add a record."""
    if name not in target:
        target[name] = {}

    if record.source_ip not in target[name]:
        target[name][record.source_ip] = {
            "total": 0,
            "spf": {"success": 0, "failure": 0},
            "dkim": {"success": 0, "failure": 0},
        }
    target[name][record.source_ip]["total"] += record.count
    for typ in ["spf", "dkim"]:
        result = getattr(record, f"{typ}_result")
        key = "success" if result == "pass" else "failure"
        target[name][record.source_ip][typ][key] += record.count


def get_aligment_stats(domain, period=None) -> dict:
    """Retrieve aligment statistics for given domain."""
    if not period:
        year, week, day = timezone.now().isocalendar()
        week -= 1
        period = f"{year}-{week}"
    else:
        year, week = period.split("-")
        if not year or not week:
            period = f"{year}-{week}"

    daterange = week_range(year, week)
    qargs = (
        Q(report__start_date__gte=daterange[0], report__start_date__lte=daterange[1])
        | Q(report__end_date__gte=daterange[0], report__end_date__lte=daterange[1])
    ) & Q(header_from=domain)
    all_records = models.Record.objects.filter(qargs)
    stats: dict = {"aligned": {}, "trusted": {}, "forwarded": {}, "failed": {}}

    dns_names = {}
    if param_tools.get_global_parameter("enable_rlookups"):
        dns_resolver = resolver.Resolver()
        dns_resolver.timeout = 1.0
        dns_resolver.lifetime = 1.0

        def get_domain_name_from_ip(ip):
            addr = reversename.from_address(ip)
            try:
                resp = dns_resolver.query(addr, "PTR")
                ext = tldextract.extract(str(resp[0].target))
                if not ext.suffix:  # invalid PTR record
                    raise resolver.NXDOMAIN()
                return (ip, ".".join((ext.domain, ext.suffix)).lower())
            except (
                resolver.NXDOMAIN,
                resolver.YXDOMAIN,
                resolver.NoAnswer,
                resolver.NoNameservers,
                resolver.Timeout,
            ):
                return (None, None)

        ips = (r.source_ip for r in all_records)
        with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
            dns_names = {
                i: n for (i, n) in list(pool.map(get_domain_name_from_ip, ips))
            }

    for record in all_records:
        name = dns_names.get(record.source_ip, _("Not resolved"))
        if record.dkim_result == "pass" and record.spf_result == "pass":
            insert_record(stats["aligned"], record, name)
        elif record.dkim_result == "pass" or record.spf_result == "pass":
            insert_record(stats["trusted"], record, name)
        elif record.reason_type == "local_policy" and record.reason_comment.startswith(
            "arc=pass"
        ):
            insert_record(stats["forwarded"], record, name)
        else:
            insert_record(stats["failed"], record, name)

    return stats
