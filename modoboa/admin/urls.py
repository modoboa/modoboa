from django.conf.urls import patterns, url


urlpatterns = patterns(
    'modoboa.admin.views',
    url(r'^$', 'index', name="index"),
    url(r'^domains/$', 'domains', name="domains"),
    (r'^domains/list/$', '_domains'),
    (r'^domains/flatlist/$', 'domains_list'),
    (r'^domains/new/', 'newdomain'),
    (r'^domains/(?P<dom_id>\d+)/edit/$', 'editdomain'),
    (r'^domains/(?P<dom_id>\d+)/delete/$', 'deldomain'),
    (r'^domains/import/$', 'import_domains'),
    (r'^domains/export/$', 'export_domains'),
    
    (r'^settings/$', 'viewsettings'),
    (r'^settings/parameters/$', 'viewparameters'),
    (r'^settings/parameters/save/$', 'saveparameters'),
    (r'^settings/extensions/$', 'viewextensions'),
    (r'^settings/extensions/save/$', 'saveextensions'),
    (r'^settings/info/$', 'information'),
    (r'^settings/logs/$', 'logs'),
    
    (r'^permissions/remove/$', 'remove_permission'),

    (r'^identities/$', 'identities'),
    (r'^identities/list/$', '_identities'),
    (r'^identities/quotas/$', 'list_quotas'),
    (r'^identities/import/$', 'import_identities'),
    (r'^identities/export/$', 'export_identities'),

    (r'^accounts/list/$', 'accounts_list'),
    (r'^accounts/new/$', 'newaccount'),
    (r'^accounts/edit/(?P<accountid>\d+)/$', 'editaccount'),
    (r'^accounts/delete/(?P<accountid>\d+)/$', 'delaccount'),

    (r'^distriblists/new/$', 'newdlist'),
    (r'^forwards/new/$', 'newforward'),

    (r'^aliases/new/$', 'newalias'),
    (r'^aliases/edit/(?P<alid>\d+)/$', 'editalias'),
    (r'^aliases/delete/$', 'delalias'),
    (r'^aliases/allowed_recipients/$', 'allowed_recipients_list'),
)
