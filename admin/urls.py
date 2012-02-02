from django.conf.urls.defaults import *

urlpatterns = patterns(
    'modoboa.admin.views',
    url(r'^$', 'domains', name="index"),
    url(r'^domains/$', 'domains', name="domains"),
    (r'^domains/new/', 'newdomain'),
    (r'^domains/(?P<dom_id>\d+)/edit/$', 'editdomain'),
    (r'^domains/delete/$', 'deldomain'),
    (r'^domains/import/$', 'importdata'),
    
    (r'^domaliases/$', "domaliases"),
    (r'^domaliases/new/', 'newdomalias'),
    (r'^domaliases/edit/(?P<alias_id>\d+)/', 'editdomalias'),
    (r'^domaliases/delete/$', 'deldomalias'),
    
    (r'^mailboxes/$', 'mailboxes'),
    (r'^mailboxes/new/$', 'newmailbox'),
    (r'^mailboxes/edit/(?P<mbox_id>\d+)/$', 'editmailbox'),
    (r'^mailboxes/delete/$', 'delmailbox'),
    (r'^mailboxes/search/$', 'mailboxes_search'),
    
    (r'^mbaliases/$', 'mbaliases'),
    (r'^mbaliases/new/$', 'newmbalias'),
    (r'^mbaliases/edit/(?P<alias_id>\d+)/$', 'editmbalias'),
    (r'^mbaliases/delete/$', 'delmbalias'),
    
    (r'^settings/$', 'viewparameters'),
    (r'^settings/parameters/$', 'viewparameters'),
    (r'^settings/parameters/save/$', 'saveparameters'),
    (r'^settings/extensions/$', 'viewextensions'),
    (r'^settings/extensions/save/$', 'saveextensions'),
    
    (r'^permissions/$', 'permissions'),
    (r'^permissions/add/$', 'add_permission'),
    (r'^permissions/domainadmin/new/$', 'create_domain_admin'),
    (r'^permissions/domainadmin/edit/(?P<da_id>\d+)/$', 'edit_domain_admin'),
    (r'^permissions/domainadmin/promote/$', 'domain_admin_promotion'),
    (r'^permissions/domainadmin/assign/(?P<da_id>\d+)/$', 'assign_domains_to_admin'),
    (r'^permissions/domainadmins/(?P<dom_id>\d+)/$', 'view_domain_admins'),
    (r'^permissions/searchaccount/$', 'search_account'),
    (r'^permissions/delete/$', 'delete_permissions'),
    )
