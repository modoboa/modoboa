from django.conf.urls.defaults import *

extpatterns = [
        (r'^$', 'index'),
        (r'^listing/$', '_listing'),
        (r'^getmailcontent/(?P<mail_id>[\w\-\+]+)/$', 'getmailcontent'),
        (r'^(?P<mail_id>[\w\-\+]+)/headers/$', 'viewheaders'),
        (r'^process/$', 'process'),
        (r'^delete/(?P<mail_id>[\w\-\+]+)/$', 'delete'),
        (r'^release/(?P<mail_id>[\w\-\+]+)/$', 'release'),
        (r'^(?P<mail_id>[\w\-\+]+)/$', 'viewmail')
        ]

urlpatterns = patterns('mailng.extensions.amavis_quarantine.views',
		       *extpatterns
                       )
