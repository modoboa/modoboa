"""App related urls."""

from django.urls import path

from . import views

app_name = "dnstools"

urlpatterns = [
    path('dnsrecords/<int:pk>/', views.DNSRecordDetailView.as_view(),
         name="dns_record_detail"),
    path('dnsrecords/autoconfig/<int:pk>/',
         views.AutoConfigRecordsStatusView.as_view(),
         name="autoconfig_records_status"),
    path('configuration/<int:pk>/',
         views.DomainDNSConfigurationView.as_view(),
         name="domain_dns_configuration"),
]
