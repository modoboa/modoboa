"""Admin urls."""

from django.urls import path

from . import views
from .views import (
    alias as alias_views, domain as domain_views, export as export_views,
    identity as identity_views, import_ as import_views
)

app_name = "admin"

urlpatterns = [
    path('', domain_views.index, name="index"),
    path('domains/', domain_views.domains, name="domain_list"),
    path('domains/<int:pk>/', views.DomainDetailView.as_view(),
         name="domain_detail"),
    path('domains/<int:pk>/alarms/', views.DomainAlarmsView.as_view(),
         name="domain_alarms"),
    path('domains/<int:pk>/dnsbl/', views.DNSBLDomainDetailView.as_view(),
         name="dnsbl_domain_detail"),
    path('domains/<int:pk>/mx/', views.MXDomainDetailView.as_view(),
         name="mx_domain_detail"),
    path('domains/list/', domain_views._domains, name="_domain_list"),
    path('domains/quotas/', domain_views.list_quotas,
         name="domain_quota_list"),
    path('domains/logs/', domain_views.list_logs,
         name="domain_logs_list"),
    path('domains/flatlist/', domain_views.domains_list,
         name="domain_flat_list"),
    path('domains/new/', domain_views.newdomain, name="domain_add"),
    path('domains/<int:dom_id>/edit/', domain_views.editdomain,
         name="domain_change"),
    path('domains/<int:dom_id>/delete/', domain_views.deldomain,
         name="domain_delete"),
    path('domains/page/', domain_views.get_next_page,
         name="domain_page"),
]

urlpatterns += [
    path('permissions/remove/', identity_views.remove_permission,
         name="permission_remove"),

    path('identities/', identity_views.identities, name="identity_list"),
    path('identities/list/', identity_views._identities,
         name="_identity_list"),
    path('identities/quotas/', identity_views.list_quotas,
         name="identity_quota_list"),
    path('identities/page/', identity_views.get_next_page,
         name="identity_page"),

    path('accounts/list/', identity_views.accounts_list,
         name="account_list"),
    path('accounts/new/', identity_views.newaccount, name="account_add"),
    path('accounts/<int:pk>/', views.AccountDetailView.as_view(),
         name="account_detail"),
    path('accounts/<int:pk>/edit/', identity_views.editaccount,
         name="account_change"),
    path('accounts/<int:pk>/delete/', identity_views.delaccount,
         name="account_delete"),
]

urlpatterns += [
    path('aliases/new/', alias_views.newalias, name="alias_add"),
    path('aliases/<int:pk>/', views.AliasDetailView.as_view(),
         name="alias_detail"),
    path('aliases/<int:alid>/edit/', alias_views.editalias,
         name="alias_change"),
    path('aliases/delete/', alias_views.delalias, name="alias_delete"),
]

urlpatterns += [
    path('domains/import/', import_views.import_domains,
         name="domain_import"),
    path('identities/import/', import_views.import_identities,
         name="identity_import"),
]

urlpatterns += [
    path('domains/export/', export_views.export_domains,
         name="domain_export"),
    path('identities/export/', export_views.export_identities,
         name="identity_export"),
]
