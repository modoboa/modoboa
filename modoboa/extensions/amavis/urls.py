from django.conf.urls.defaults import *

urlpatterns = patterns(
    'modoboa.extensions.amavis.views',
    (r'^$', 'index'),
    (r'^listing/$', '_listing'),
    (r'^getmailcontent/(?P<mail_id>[\w\-\+]+)/$', 'getmailcontent'),
    (r'^process/$', 'process'),
    (r'^nbrequests/$', 'nbrequests'),
    (r'^delete/(?P<mail_id>[\w\-\+]+)/$', 'delete'),
    (r'^release/(?P<mail_id>[\w\-\+]+)/$', 'release'),
    (r'^(?P<mail_id>[\w\-\+]+)/$', 'viewmail'),
    (r'^(?P<mail_id>[\w\-\+]+)/headers/$', 'viewheaders'),
    )
