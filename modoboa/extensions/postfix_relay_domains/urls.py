from django.conf.urls import patterns, url

urlpatterns = patterns(
    'modoboa.extensions.postfix_relay_domains.views',
    (r'^relaydomains/new/', 'create'),
    url(r'^relaydomains/(?P<rdom_id>\d+)/edit/$', 'edit',
        name='edit_relaydomain'),
    (r'^relaydomains/(?P<rdom_id>\d+)/delete/$', 'delete'),
    (r'^relaydomains/scan_services/$', 'scan_for_services'),
)
