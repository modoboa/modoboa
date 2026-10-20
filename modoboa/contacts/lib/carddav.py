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
from urllib.parse import urlparse

from caldav.elements import base as elements_base, dav as elements_dav
import lxml.etree as ET
import requests


def _safe_xml(xml):
    """Parse XML with a hardened parser that disables entity resolution.

    Protects against XML-based attacks (billion laughs, XXE, etc.). A new
    parser is created for each call since lxml parsers are not thread-safe.
    """
    parser = ET.XMLParser(resolve_entities=False, no_network=True)
    return ET.XML(xml, parser=parser)


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


class Mkcol(elements_base.BaseElement):
    tag = ns("CARD", "mkcol")


class AddressBook(elements_base.BaseElement):
    tag = ns("CARD", "addressbook")


class Etag(elements_base.BaseElement):
    tag = ns("D", "getetag")


class SyncToken(elements_base.BaseElement):
    tag = ns("D", "sync-token")


class SyncLevel(elements_base.BaseElement):
    tag = ns("D", "sync-level")


class SyncCollectionQuery(elements_base.BaseElement):
    tag = ns("D", "sync-collection")


class PyCardDAV:
    """class for interacting with a CardDAV server

    raises:
        requests.exceptions.SSLError
        requests.exceptions.ConnectionError
        more requests.exceptions depending on the actual error
        Exception if the URL is not a CardDAV resource
    """

    def __init__(
        self,
        resource,
        user="",
        passwd="",
        verify=True,
        write_support=False,
        auth="basic",
        timeout=10,
    ):
        split_url = urlparse(resource)
        url_tuple = namedtuple("url", "resource base path")
        self.url = url_tuple(
            resource, split_url.scheme + "://" + split_url.netloc, split_url.path
        )
        self.session = requests.session()
        self.write_support = write_support
        self._settings = {"verify": verify, "timeout": timeout}
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
            elements_dav.Set()
            + [
                elements_dav.Prop()
                + [
                    elements_dav.ResourceType()
                    + elements_dav.Collection()
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

    def sync_vcards(self, sync_token=None):
        """Synchronize vcards using webdav sync."""
        data = (
            SyncCollectionQuery()
            + [elements_dav.Prop() + Etag()]
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

    def update_vcard(self, card, filename, etag):
        """
        pushes changed vcard to the server
        card: vcard as unicode string
        etag: str or None, if this is set to a non-empty string, card is only
              updated if remote etag matches. Otherwise the update is forced
        :returns: the new etag, empty if the server did not return it
        """
        self._check_write_support()
        remotepath = str(self.url.resource + "/" + filename)
        headers = self.headers
        headers["content-type"] = "text/vcard"
        if etag:
            headers["If-Match"] = etag
        response = self.session.put(
            remotepath, data=card, headers=headers, **self._settings
        )
        response.raise_for_status()
        return response.headers.get("etag", "")

    def delete_vcard(self, filename, etag):
        """deletes vcard from server

        deletes the resource at href if etag matches,
        if etag=None delete anyway
        :param filename: name of the card resource to be deleted
        :type filename: str()
        :param etag: etag of that card, if empty card is always deleted
        :type href: str()
        :returns: nothing
        """
        self._check_write_support()
        remotepath = str(self.url.resource + "/" + filename)
        headers = self.headers
        headers["content-type"] = "text/vcard"
        if etag:
            headers["If-Match"] = etag
        response = self.session.delete(remotepath, headers=headers, **self._settings)
        # Card already gone on the server: nothing left to delete
        if response.status_code != 404:
            response.raise_for_status()

    def upload_new_card(self, filename, card):
        """
        upload new card to the server

        :param card: vcard to be uploaded
        :type card: unicode
        :rtype: tuple of string (path of the vcard on the server) and etag of
                new card (string or None)
        """
        self._check_write_support()
        card = card.encode("utf-8")
        remotepath = str(self.url.resource + "/" + filename)
        headers = self.headers
        headers["content-type"] = "text/vcard"
        headers["If-None-Match"] = "*"
        response = self.session.put(
            remotepath, data=card, headers=headers, **self._settings
        )
        response.raise_for_status()
        etag = response.headers.get("etag", "")
        return (urlparse(remotepath).path, etag)

    def __process_report_result(self, xml):
        """Parse REPORT query result and return a dict."""
        result = {"cards": []}
        ns = "{DAV:}"
        element = _safe_xml(xml)
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
