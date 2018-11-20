"""App related urls."""

from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^dnsrecords/(?P<pk>\d+)/$', views.DNSRecordDetailView.as_view(),
        name="dns_record_detail"),
    url(r'^dnsrecords/autoconfig/(?P<pk>\d+)/$',
        views.AutoConfigRecordsStatusView.as_view(),
        name="autoconfig_records_status"),
    url(r'^configuration/(?P<pk>\d+)/$',
        views.DomainDNSConfigurationView.as_view(),
        name="domain_dns_configuration"),
]
