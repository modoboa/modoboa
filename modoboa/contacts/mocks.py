"""Mocks to test the contacts plugin."""

import httmock


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


@httmock.urlmatch(method="PROPFIND")
def propfind_mock(url, request):
    """Simulate a PROPFIND request."""
    content = b"""
<d:multistatus xmlns:d="DAV:" xmlns:cs="http://calendarserver.org/ns/">
    <d:response>
        <d:href>/radicale/user@test.com/contacts/</d:href>
        <d:propstat>
            <d:prop>
                <d:sync-token>http://modoboa.org/ns/sync-token/3145</d:sync-token>
            </d:prop>
            <d:status>HTTP/1.1 200 OK</d:status>
        </d:propstat>
    </d:response>
</d:multistatus>
"""
    return {"status_code": 200, "content": content}


@httmock.urlmatch(method="REPORT")
def report_mock(url, request):
    """Simulate a REPORT request."""
    if url.path.endswith(".vcf"):
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
 </d:multistatus>
"""
    else:
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


@httmock.urlmatch(method="GET")
def get_mock(url, request):
    """Simulate a GET request."""
    uid = url.path.split("/")[-1]
    content = f"""
BEGIN:VCARD
VERSION:3.0
UID:{uid}
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
    return {"status_code": 200, "content": content}
