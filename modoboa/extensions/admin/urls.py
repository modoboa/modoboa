from django.conf.urls import patterns, url


urlpatterns = patterns(
    'modoboa.extensions.admin.views.domain',
    (r'^$', 'index'),
    url(r'^domains/$', 'domains', name="domains"),
    (r'^domains/list/$', '_domains'),
    (r'^domains/flatlist/$', 'domains_list'),
    url(r'^domains/new/', 'newdomain', name='new_domain'),
    url(r'^domains/(?P<dom_id>\d+)/edit/$', 'editdomain', name="edit_domain"),
    (r'^domains/(?P<dom_id>\d+)/delete/$', 'deldomain'),
)

urlpatterns += patterns(
    'modoboa.extensions.admin.views.identity',
    (r'^permissions/remove/$', 'remove_permission'),

    (r'^identities/$', 'identities'),
    (r'^identities/list/$', '_identities'),
    (r'^identities/quotas/$', 'list_quotas'),

    (r'^accounts/list/$', 'accounts_list'),
    url(r'^accounts/new/$', 'newaccount', name="new_account"),
    url(r'^accounts/edit/(?P<accountid>\d+)/$', 'editaccount',
        name="edit_account"),
    (r'^accounts/delete/(?P<accountid>\d+)/$', 'delaccount'),
)

urlpatterns += patterns(
    'modoboa.extensions.admin.views.alias',
    (r'^distriblists/new/$', 'newdlist'),
    (r'^forwards/new/$', 'newforward'),

    (r'^aliases/new/$', 'newalias'),
    (r'^aliases/edit/(?P<alid>\d+)/$', 'editalias'),
    (r'^aliases/delete/$', 'delalias'),
)

urlpatterns += patterns(
    'modoboa.extensions.admin.views.import',
    (r'^domains/import/$', 'import_domains'),
    (r'^identities/import/$', 'import_identities'),
)

urlpatterns += patterns(
    'modoboa.extensions.admin.views.export',
    (r'^domains/export/$', 'export_domains'),
    (r'^identities/export/$', 'export_identities'),
)
