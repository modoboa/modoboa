# -*- coding: utf-8 -*-

from django import http


def test_view(request):
    return http.HttpResponse()
