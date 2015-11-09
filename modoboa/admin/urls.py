from django.conf.urls import patterns, url


urlpatterns = patterns(
    'modoboa.admin.views.domain',

    url(r'^$', 'index', name="index"),
    url(r'^domains/$', 'domains', name="domain_list"),
    url(r'^domains/list/$', '_domains', name="_domain_list"),
    url(r'^domains/flatlist/$', 'domains_list', name="domain_flat_list"),
    url(r'^domains/stats/$', 'domain_statistics', name="domain_statistics"),
    url(r'^domains/new/', 'newdomain', name='domain_add'),
    url(r'^domains/(?P<dom_id>\d+)/edit/$', 'editdomain',
        name="domain_change"),
    url(r'^domains/(?P<dom_id>\d+)/delete/$', 'deldomain',
        name="domain_delete"),
)

urlpatterns += patterns(
    'modoboa.admin.views.identity',

    url(r'^permissions/remove/$', 'remove_permission',
        name="permission_remove"),

    url(r'^identities/$', 'identities', name="identity_list"),
    url(r'^identities/list/$', '_identities', name="_identity_list"),
    url(r'^identities/quotas/$', 'list_quotas', name="quota_list"),
    url(r'^identities/page/$', 'get_next_page', name="identity_page"),

    url(r'^accounts/list/$', 'accounts_list', name="account_list"),
    url(r'^accounts/new/$', 'newaccount', name="account_add"),
    url(r'^accounts/edit/(?P<accountid>\d+)/$', 'editaccount',
        name="account_change"),
    url(r'^accounts/delete/(?P<accountid>\d+)/$', 'delaccount',
        name="account_delete"),
)

urlpatterns += patterns(
    'modoboa.admin.views.alias',

    url(r'^distriblists/new/$', 'newdlist', name="dlist_add"),
    url(r'^forwards/new/$', 'newforward', name="forward_add"),

    url(r'^aliases/new/$', 'newalias', name="alias_add"),
    url(r'^aliases/edit/(?P<alid>\d+)/$', 'editalias', name="alias_change"),
    url(r'^aliases/delete/$', 'delalias', name="alias_delete"),
)

urlpatterns += patterns(
    'modoboa.admin.views.import_',

    url(r'^domains/import/$', 'import_domains', name="domain_import"),
    url(r'^identities/import/$', 'import_identities', name="identity_import"),
)

urlpatterns += patterns(
    'modoboa.admin.views.export',

    url(r'^domains/export/$', 'export_domains', name="domain_export"),
    url(r'^identities/export/$', 'export_identities', name="identity_export"),
)
