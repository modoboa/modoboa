from django.conf.urls import patterns

urlpatterns = patterns(
    'modoboa.extensions.postfix_relay_domains.views',
    (r'^relaydomains/new/', 'create'),
    (r'^relaydomains/(?P<rdom_id>\d+)/edit/$', 'edit'),
    (r'^relaydomains/(?P<rdom_id>\d+)/delete/$', 'delete'),
    (r'^relaydomains/scan_services/$', 'scan_for_services'),
)
