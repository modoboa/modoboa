from django.conf.urls import patterns

urlpatterns = patterns(
    'modoboa.extensions.amavis.views',
    (r'^$', 'index'),
    (r'^listing/$', '_listing'),
    (r'^getmailcontent/(?P<mail_id>[\w\-\+]+)/$', 'getmailcontent'),
    (r'^process/$', 'process'),
    (r'^nbrequests/$', 'nbrequests'),
    (r'^delete/(?P<mail_id>[\w\-\+]+)/$', 'delete'),
    (r'^release/(?P<mail_id>[\w\-\+]+)/$', 'release'),
    (r'^markspam/(?P<mail_id>[\w\-\+]+)/$', 'mark_as_spam'),
    (r'^markham/(?P<mail_id>[\w\-\+]+)/$', 'mark_as_ham'),
    (r'^learning_recipient/$', 'learning_recipient'),
    (r'^(?P<mail_id>[\w\-\+]+)/$', 'viewmail'),
    (r'^(?P<mail_id>[\w\-\+]+)/headers/$', 'viewheaders'),
)
