"""Mocks to test the contacts plugin."""

from xml.sax.saxutils import escape

import httmock
from lxml import etree


@httmock.urlmatch(method="OPTIONS")
def options_mock(url, request):
    """Simulate options request."""
    return {"status_code": 200, "headers": {"DAV": "addressbook"}}


@httmock.urlmatch(method="MKCOL")
def mkcol_mock(url, request):
    """Simulate collection creation."""
    return {"status_code": 201}


@httmock.urlmatch(method="DELETE")
def delete_mock(url, request):
    """Simulate a DELETE request."""
    return {"status_code": 204}


@httmock.urlmatch(method="PUT")
def put_mock(url, request):
    """Simulate a PUT request."""
    return {"status_code": 200, "headers": {"etag": '"12345"'}}


@httmock.urlmatch(method="REPORT")
def report_mock(url, request):
    """Simulate a REPORT request."""
    if b"addressbook-multiget" in request.body:
        return multiget_response(request.body)
    content = b"""
<d:multistatus xmlns:d="DAV:">
    <d:response>
        <d:href>/radicale/user@test.com/contacts/newcard.vcf</d:href>
        <d:propstat>
            <d:prop>
                <d:getetag>"33441-34321"</d:getetag>
            </d:prop>
            <d:status>HTTP/1.1 200 OK</d:status>
        </d:propstat>
    </d:response>
    <d:response>
        <d:href>/radicale/user@test.com/contacts/updatedcard.vcf</d:href>
        <d:propstat>
            <d:prop>
                <d:getetag>"33541-34696"</d:getetag>
            </d:prop>
            <d:status>HTTP/1.1 200 OK</d:status>
        </d:propstat>
    </d:response>
    <d:response>
        <d:href>/radicale/user@test.com/contacts/deletedcard.vcf</d:href>
        <d:status>HTTP/1.1 404 Not Found</d:status>
    </d:response>
    <d:sync-token>http://modoboa.org/ns/sync/5001</d:sync-token>
 </d:multistatus>
"""
    return {"status_code": 200, "content": content}


def vcard(filename):
    """Return the vCard stored under filename."""
    return f"""BEGIN:VCARD
VERSION:3.0
UID:{filename}
N:Gump;Forrest
FN:Forrest Gump
ORG:Bubba Gump Shrimp Co.
TITLE:Shrimp Man
TEL;TYPE=WORK;VOICE:(111) 555-1212
TEL;TYPE=HOME;VOICE:(404) 555-1212
ADR;TYPE=HOME:;;42 Plantation St.;Baytown;LA;30314;United States of America
EMAIL;TYPE=PREF,INTERNET:forrestgump@example.com
END:VCARD
"""


def multiget_response(body, content=vcard):
    """Answer an addressbook-multiget REPORT, content(filename) gives each card."""
    hrefs = [element.text for element in etree.fromstring(body).iter("{DAV:}href")]
    responses = "".join(
        f"""<d:response>
    <d:href>{href}</d:href>
    <d:propstat>
        <d:prop>
            <d:getetag>"1"</d:getetag>
            <card:address-data>{escape(content(href.split("/")[-1]))}</card:address-data>
        </d:prop>
        <d:status>HTTP/1.1 200 OK</d:status>
    </d:propstat>
</d:response>"""
        for href in hrefs
    )
    content = (
        '<d:multistatus xmlns:d="DAV:" xmlns:card="urn:ietf:params:xml:ns:carddav">'
        f"{responses}</d:multistatus>"
    )
    return {"status_code": 207, "content": content.encode()}
