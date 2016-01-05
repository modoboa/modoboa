from django.conf.urls import patterns, url

urlpatterns = patterns(
    'modoboa.relaydomains.views',

    url(r'^scan_services/$', 'scan_for_services',
        name="service_scan"),
)
