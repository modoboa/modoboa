# vim: set ts=4 sw=4 expandtab sts=4:
# Copyright (c) 2011-2014 Christian Geier & contributors
# Copyright (c) 2018 Antoine Nguyen <tonio@ngyn.org>
#
# Permission is hereby granted, free of charge, to any person obtaining
# a copy of this software and associated documentation files (the
# "Software"), to deal in the Software without restriction, including
# without limitation the rights to use, copy, modify, merge, publish,
# distribute, sublicense, and/or sell copies of the Software, and to
# permit persons to whom the Software is furnished to do so, subject to
# the following conditions:
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE
# LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION
# OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION
# WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
contains the class PyCardDAv and some associated functions and definitions
"""

from collections import namedtuple
import logging

from six.moves import urllib

from caldav import elements
import lxml.etree as ET
import requests


class UploadFailed(Exception):
    """uploading the card failed"""

    pass


class NoWriteSupport(Exception):
    """write support has not been enabled"""

    pass


nsmap = {
    "D": "DAV:",
    "CARD": "urn:ietf:params:xml:ns:carddav",
}


def ns(prefix, tag=None):
    name = f"{{{nsmap[prefix]}}}"
    if tag is not None:
        name = f"{name}{tag}"
    return name


class Mkcol(elements.base.BaseElement):
    tag = ns("CARD", "mkcol")


class AddressBook(elements.base.BaseElement):
    tag = ns("CARD", "addressbook")


class AddressBookQuery(elements.base.BaseElement):
    tag = ns("CARD", "addressbook-query")


class AddressData(elements.base.BaseElement):
    tag = ns("CARD", "address-data")


class Etag(elements.base.BaseElement):
    tag = ns("D", "getetag")


class SyncToken(elements.base.BaseElement):
    tag = ns("D", "sync-token")


class SyncLevel(elements.base.BaseElement):
    tag = ns("D", "sync-level")


class SyncCollectionQuery(elements.base.BaseElement):
    tag = ns("D", "sync-collection")


class PyCardDAV:
    """class for interacting with a CardDAV server

    Since PyCardDAV relies heavily on Requests [1] its SSL verification is also
    shared by PyCardDAV [2]. For now, only the *verify* keyword is exposed
    through PyCardDAV.

    [1] http://docs.python-requests.org/
    [2] http://docs.python-requests.org/en/latest/user/advanced/

    raises:
        requests.exceptions.SSLError
        requests.exceptions.ConnectionError
        more requests.exceptions depending on the actual error
        Exception (shame on me)

    """

    def __init__(
        self,
        resource,
        debug="",
        user="",
        passwd="",
        verify=True,
        write_support=False,
        auth="basic",
    ):
        # shutup urllib3
        urllog = logging.getLogger("requests.packages.urllib3.connectionpool")
        urllog.setLevel(logging.CRITICAL)
        urllog = logging.getLogger("urllib3.connectionpool")
        urllog.setLevel(logging.CRITICAL)

        # activate pyopenssl if available
        try:
            import urllib3.contrib.pyopenssl
        except ImportError:
            pass
        else:
            urllib3.contrib.pyopenssl.inject_into_urllib3()

        split_url = urllib.parse.urlparse(resource)
        url_tuple = namedtuple("url", "resource base path")
        self.url = url_tuple(
            resource, split_url.scheme + "://" + split_url.netloc, split_url.path
        )
        self.debug = debug
        self.session = requests.session()
        self.write_support = write_support
        self._settings = {"verify": verify}
        if auth == "basic":
            self._settings["auth"] = (
                user,
                passwd,
            )
        if auth == "digest":
            from requests.auth import HTTPDigestAuth

            self._settings["auth"] = HTTPDigestAuth(user, passwd)
        self._default_headers = {"User-Agent": "pyCardDAV"}

        headers = self.headers
        headers["Depth"] = "1"
        response = self.session.request(
            "OPTIONS", self.url.resource, headers=headers, **self._settings
        )
        response.raise_for_status()  # raises error on not 2XX HTTP status code
        if "addressbook" not in response.headers.get("DAV", ""):
            raise Exception("URL is not a CardDAV resource")

    @property
    def verify(self):
        """gets verify from settings dict"""
        return self._settings["verify"]

    @verify.setter
    def verify(self, verify):
        """set verify"""
        self._settings["verify"] = verify

    @property
    def headers(self):
        """returns the headers"""
        return dict(self._default_headers)

    def _check_write_support(self):
        """checks if user really wants his data destroyed"""
        if not self.write_support:
            raise NoWriteSupport

    def create_abook(self):
        """Create a new address book."""
        self._check_write_support()
        data = Mkcol() + [
            elements.dav.Set()
            + [
                elements.dav.Prop()
                + [
                    elements.dav.ResourceType()
                    + elements.dav.Collection()
                    + AddressBook()
                ]
            ]
        ]
        body = ET.tostring(data.xmlelement(), encoding="utf-8", xml_declaration=True)
        response = self.session.request(
            "MKCOL",
            self.url.resource,
            data=body,
            headers=self.headers,
            **self._settings,
        )
        response.raise_for_status()

    def get_abook(self):
        """does the propfind and processes what it returns

        :rtype: list of hrefs to vcards
        """
        xml = self._get_xml_props()
        abook = self._process_xml_props(xml)
        return abook

    def get_vcard(self, href):
        """
        pulls vcard from server

        :returns: vcard
        :rtype: string
        """
        response = self.session.get(
            self.url.base + href, headers=self.headers, **self._settings
        )
        response.raise_for_status()
        return response.content

    def get_sync_token(self):
        """Retrieve the current sync token."""
        headers = self.headers
        headers["Depth"] = "0"
        data = elements.dav.Propfind() + [elements.dav.Prop() + SyncToken()]
        body = ET.tostring(data.xmlelement(), encoding="utf-8", xml_declaration=True)
        response = self.session.request(
            "PROPFIND", self.url.resource, data=body, headers=headers, **self._settings
        )
        response.raise_for_status()
        abook = self._process_xml_props(response.content)
        return abook["sync-token"]

    def sync_vcards(self, sync_token=None):
        """Synchronize vcards using webdav sync."""
        data = (
            SyncCollectionQuery()
            + [elements.dav.Prop() + Etag()]
            + SyncToken(value=sync_token)
            + SyncLevel(value="1")
        )
        body = ET.tostring(data.xmlelement(), encoding="utf-8", xml_declaration=True)
        response = self.session.request(
            "REPORT",
            self.url.resource,
            data=body,
            headers=self.headers,
            **self._settings,
        )
        response.raise_for_status()
        return self.__process_report_result(response.content)

    def update_vcard(self, card, uid, etag):
        """
        pushes changed vcard to the server
        card: vcard as unicode string
        etag: str or None, if this is set to a string, card is only updated if
              remote etag matches. If etag = None the update is forced anyway
        """
        # TODO what happens if etag does not match?
        self._check_write_support()
        remotepath = str(self.url.resource + "/" + uid)
        headers = self.headers
        headers["content-type"] = "text/vcard"
        if etag is not None:
            headers["If-Match"] = etag
        response = self.session.put(
            remotepath, data=card, headers=headers, **self._settings
        )
        if not response.ok:
            response.raise_for_status()
        # Now retrieve the new etag
        data = AddressBookQuery() + [elements.dav.Prop() + Etag()]
        body = ET.tostring(data.xmlelement(), encoding="utf-8", xml_declaration=True)
        response = self.session.request(
            "REPORT", remotepath, data=body, headers=self.headers, **self._settings
        )
        response.raise_for_status()
        return self.__process_report_result(response.content)

    def delete_vcard(self, uid, etag):
        """deletes vcard from server

        deletes the resource at href if etag matches,
        if etag=None delete anyway
        :param uid: UID of card to be deleted
        :type uid: str()
        :param etag: etag of that card, if None card is always deleted
        :type href: str()
        :returns: nothing
        """
        # TODO: what happens if etag does not match, url does not exist etc ?
        self._check_write_support()
        remotepath = str(self.url.resource + "/" + uid)
        headers = self.headers
        headers["content-type"] = "text/vcard"
        if etag is not None:
            headers["If-Match"] = etag
        response = self.session.delete(remotepath, headers=headers, **self._settings)
        response.raise_for_status()

    def upload_new_card(self, uid, card):
        """
        upload new card to the server

        :param card: vcard to be uploaded
        :type card: unicode
        :rtype: tuple of string (path of the vcard on the server) and etag of
                new card (string or None)
        """
        self._check_write_support()
        card = card.encode("utf-8")
        remotepath = str(self.url.resource + "/" + uid)
        headers = self.headers
        headers["content-type"] = "text/vcard"  # TODO perhaps this should
        # be set to the value this carddav server uses itself
        headers["If-None-Match"] = "*"
        response = requests.put(
            remotepath, data=card, headers=headers, **self._settings
        )
        if response.ok:
            parsed_url = urllib.parse.urlparse(remotepath)
            etag = response.headers.get("etag", "")
            return (parsed_url.path, etag)
        response.raise_for_status()

    def __process_report_result(self, xml):
        """Parse REPORT query result and return a dict."""
        result = {"cards": []}
        ns = "{DAV:}"
        element = ET.XML(xml)
        for item in element.iterchildren():
            if item.tag != ns + "response":
                result["token"] = item.text
                continue
            card = {}
            for d in item.iterdescendants():
                if d.tag == ns + "href":
                    card["href"] = d.text
                elif d.tag == ns + "status":
                    card["status"] = d.text
                elif d.tag == ns + "getetag":
                    card["etag"] = d.text
            result["cards"].append(card)
        return result

    def _get_xml_props(self):
        """PROPFIND method

        gets the xml file with all vcard hrefs

        :rtype: str() (an xml file)
        """
        headers = self.headers
        headers["Depth"] = "0"
        response = self.session.request(
            "PROPFIND", self.url.resource, headers=headers, **self._settings
        )
        response.raise_for_status()
        return response.content

    @classmethod
    def _process_xml_props(cls, xml):
        """processes the xml from PROPFIND, listing all vcard hrefs

        :param xml: the xml file
        :type xml: str()
        :rtype: dict() key: href, value: etag
        """
        namespace = "{DAV:}"

        element = ET.XML(xml)
        abook = dict()
        for response in element.iterchildren():
            if response.tag != namespace + "response":
                continue
            href = ""
            etag = ""
            insert = False
            for refprop in response.iterchildren():
                if refprop.tag == namespace + "href":
                    href = refprop.text
                for prop in refprop.iterchildren():
                    for props in prop.iterchildren():
                        # different servers give different getcontenttypes:
                        # e.g.:
                        #  "text/vcard"
                        #  "text/x-vcard"
                        #  "text/x-vcard; charset=utf-8"
                        #  "text/directory;profile=vCard"
                        #  "text/directory"
                        #  "text/vcard; charset=utf-8"  CalendarServer
                        if (
                            props.tag == namespace + "getcontenttype"
                            and props.text.split(";")[0].strip()
                            in ["text/vcard", "text/x-vcard"]
                        ):
                            insert = True
                        if (
                            props.tag == namespace + "resourcetype"
                            and namespace + "collection"
                            in [c.tag for c in props.iterchildren()]
                        ):
                            insert = False
                            break
                        if props.tag == namespace + "getetag":
                            etag = props.text
                            break
                        if props.tag == namespace + "sync-token":
                            abook["sync-token"] = props.text
                    if insert:
                        abook[href] = etag
        return abook
