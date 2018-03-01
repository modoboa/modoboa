# -*- coding: utf-8 -*-

"""Admin urls."""

from __future__ import unicode_literals

from django.conf.urls import url

from . import views
from .views import (
    alias as alias_views, domain as domain_views, export as export_views,
    identity as identity_views, import_ as import_views
)

urlpatterns = [
    url(r'^$', domain_views.index, name="index"),
    url(r'^domains/$', domain_views.domains, name="domain_list"),
    url(r'^domains/(?P<pk>\d+)/$', views.DomainDetailView.as_view(),
        name="domain_detail"),
    url(r'^domains/(?P<pk>\d+)/dnsbl/$', views.DNSBLDomainDetailView.as_view(),
        name="dnsbl_domain_detail"),
    url(r'^domains/(?P<pk>\d+)/mx/$', views.MXDomainDetailView.as_view(),
        name="mx_domain_detail"),
    url(r'^domains/list/$', domain_views._domains, name="_domain_list"),
    url(r'^domains/quotas/$', domain_views.list_quotas,
        name="domain_quota_list"),
    url(r'^domains/flatlist/$', domain_views.domains_list,
        name="domain_flat_list"),
    url(r'^domains/new/', domain_views.newdomain, name="domain_add"),
    url(r'^domains/(?P<dom_id>\d+)/edit/$', domain_views.editdomain,
        name="domain_change"),
    url(r'^domains/(?P<dom_id>\d+)/delete/$', domain_views.deldomain,
        name="domain_delete"),
    url(r'^domains/page/$', domain_views.get_next_page,
        name="domain_page"),
]

urlpatterns += [
    url(r'^permissions/remove/$', identity_views.remove_permission,
        name="permission_remove"),

    url(r'^identities/$', identity_views.identities, name="identity_list"),
    url(r'^identities/list/$', identity_views._identities,
        name="_identity_list"),
    url(r'^identities/quotas/$', identity_views.list_quotas,
        name="identity_quota_list"),
    url(r'^identities/page/$', identity_views.get_next_page,
        name="identity_page"),

    url(r'^accounts/list/$', identity_views.accounts_list,
        name="account_list"),
    url(r'^accounts/new/$', identity_views.newaccount, name="account_add"),
    url(r'^accounts/(?P<pk>\d+)/$', views.AccountDetailView.as_view(),
        name="account_detail"),
    url(r'^accounts/(?P<pk>\d+)/edit/$', identity_views.editaccount,
        name="account_change"),
    url(r'^accounts/(?P<pk>\d+)/delete/$', identity_views.delaccount,
        name="account_delete"),
]

urlpatterns += [
    url(r'^aliases/new/$', alias_views.newalias, name="alias_add"),
    url(r'^aliases/(?P<pk>\d+)/$', views.AliasDetailView.as_view(),
        name="alias_detail"),
    url(r'^aliases/(?P<alid>\d+)/edit/$', alias_views.editalias,
        name="alias_change"),
    url(r'^aliases/delete/$', alias_views.delalias, name="alias_delete"),
]

urlpatterns += [
    url(r'^domains/import/$', import_views.import_domains,
        name="domain_import"),
    url(r'^identities/import/$', import_views.import_identities,
        name="identity_import"),
]

urlpatterns += [
    url(r'^domains/export/$', export_views.export_domains,
        name="domain_export"),
    url(r'^identities/export/$', export_views.export_identities,
        name="identity_export"),
]
