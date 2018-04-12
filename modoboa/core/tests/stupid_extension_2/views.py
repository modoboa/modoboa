# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from django import http


def test_view(request):
    return http.HttpResponse()
