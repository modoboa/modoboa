# coding: utf-8
from django.test import TestCase
from django.test.client import Client
from django.utils import simplejson

class ModoTestCase(TestCase):
    
    def setUp(self, username="admin", password="password"):
        self.clt = Client()
        self.assertEqual(self.clt.login(username=username, password=password), True)

    def check_ajax_request(self, method, url, params, status="ok", **kwargs):
        response = getattr(self.clt, method) \
            (url, params, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
        self.assertEqual(response.status_code, 200)
        obj = simplejson.loads(response.content)
        self.assertEqual(obj["status"], status)
        for kw, v in kwargs.iteritems():
            self.assertEqual(obj[kw], v)

    def check_ajax_post(self, *args, **kwargs):
        self.check_ajax_request("post", *args, **kwargs)

    def check_ajax_get(self, *args, **kwargs):
        self.check_ajax_request("get", *args, **kwargs)

class ExtTestCase(ModoTestCase):
    name = None

    def setUp(self, *args, **kwargs):
        super(ExtTestCase, self).setUp(*args, **kwargs)
        self.clt.get("/modoboa/admin/settings/extensions/")
        self.clt.post("/modoboa/admin/settings/extensions/save/",
                      {"select_%s" % self.name : "1"})
