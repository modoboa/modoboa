from django.conf.urls import patterns, url

urlpatterns = patterns(
    'modoboa.extensions.postfix_relay_domains.views',

    url(r'^relaydomains/new/', 'create', name="relaydomain_add"),
    url(r'^relaydomains/(?P<rdom_id>\d+)/edit/$', 'edit',
        name='relaydomain_change'),
    url(r'^relaydomains/(?P<rdom_id>\d+)/delete/$', 'delete',
        name="relaydomain_delete"),
    url(r'^relaydomains/scan_services/$', 'scan_for_services',
        name="service_scan"),
)
