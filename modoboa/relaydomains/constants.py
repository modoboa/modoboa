"""Relaydomains app constants."""

PERMISSIONS = {
    "Resellers": [
        ("relaydomains", "relaydomain", "add_relaydomain"),
        ("relaydomains", "relaydomain", "change_relaydomain"),
        ("relaydomains", "relaydomain", "delete_relaydomain"),
        ("relaydomains", "service", "add_service"),
        ("relaydomains", "service", "change_service"),
        ("relaydomains", "service", "delete_service")
    ]
}
