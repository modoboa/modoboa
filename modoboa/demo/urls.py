# coding: utf-8
from django.conf.urls import patterns

urlpatterns = patterns('modoboa.demo.views',
    (r'^sendvirus/$', 'send_virus'),
    (r'^sendspam/$', 'send_spam'),
)
