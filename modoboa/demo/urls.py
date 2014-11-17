# coding: utf-8
from django.conf.urls import patterns, url

urlpatterns = patterns(
    'modoboa.demo.views',

    url(r'^sendvirus/$', 'send_virus', name="virus_send"),
    url(r'^sendspam/$', 'send_spam', name="spam_send"),
)
