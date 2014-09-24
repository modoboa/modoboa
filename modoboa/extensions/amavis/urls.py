from django.conf.urls import patterns, url

urlpatterns = patterns(
    'modoboa.extensions.amavis.views',

    url(r'^$', 'index', name="index"),
    url(r'^listing/$', '_listing', name="_mail_list"),
    url(r'^getmailcontent/(?P<mail_id>[\w\-\+]+)/$', 'getmailcontent',
        name="mailcontent_get"),
    url(r'^process/$', 'process', name="mail_process"),
    url(r'^delete/(?P<mail_id>[\w\-\+]+)/$', 'delete', name="mail_delete"),
    url(r'^release/(?P<mail_id>[\w\-\+]+)/$', 'release',
        name="mail_release"),
    url(r'^(?P<mail_id>[\w\-\+]+)/$', 'viewmail', name="mail_detail"),
    url(r'^(?P<mail_id>[\w\-\+]+)/headers/$', 'viewheaders',
        name="headers_detail"),
)
