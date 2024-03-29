# Generated by Django 1.10.7 on 2017-11-23 15:53
from django.db import migrations


def move_relaydomain_to_transport(apps, schema_editor):
    """Transform relaydomains to transports."""
    RelayDomain = apps.get_model("relaydomains", "RelayDomain")
    RecipientAccess = apps.get_model("relaydomains", "RecipientAccess")
    Transport = apps.get_model("transport", "Transport")
    ra_to_create = []
    for rd in RelayDomain.objects.select_related("domain", "service"):
        next_hop = "[{}]:{}".format(rd.target_host, rd.target_port)
        tr = Transport.objects.create(
            pattern=rd.domain.name,
            service="relay",
            next_hop=next_hop,
            _settings={
                "relay_target_host": rd.target_host,
                "relay_target_port": rd.target_port,
                "relay_verify_recipients": rd.verify_recipients,
            },
        )
        rd.domain.transport = tr
        rd.domain.save(update_fields=["transport"])
        if not rd.verify_recipients:
            continue
        ra_to_create.append(
            RecipientAccess(
                pattern=rd.domain.name, action="reject_unverified_recipient"
            )
        )
    RecipientAccess.objects.bulk_create(ra_to_create)


def forward(apps, schema_editor):
    """Empty."""
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("relaydomains", "0007_recipientaccess"),
        ("transport", "0001_initial"),
        ("admin", "0011_domain_transport"),
    ]

    operations = [migrations.RunPython(move_relaydomain_to_transport, forward)]
