from django.conf.urls.defaults import *

urlpatterns = patterns('modoboa.admin.views',
                       url(r'^$', 'domains', name="index"),
                       url(r'^domains/$', 'domains', name="domains"),
                       (r'^domains/new/', 'newdomain'),
                       (r'^domains/(?P<dom_id>\d+)/edit/$', 'editdomain'),
                       (r'^domains/delete/$', 'deldomain'),

                       (r'^domaliases/$', "domaliases"),
                       (r'^domaliases/new/', 'newdomalias'),
                       (r'^domaliases/edit/(?P<alias_id>\d+)/', 'editdomalias'),
                       (r'^domaliases/delete/$', 'deldomalias'),

                       (r'^mailboxes/$', 'mailboxes'),
                       (r'^mailboxes/new/$', 'newmailbox'),
                       (r'^mailboxes/edit/(?P<mbox_id>\d+)/$', 'editmailbox'),
                       (r'^mailboxes/delete/$', 'delmailbox'),
                       
                       (r'^mbaliases/$', 'mbaliases'),
                       (r'^mbaliases/new/$', 'newmbalias'),
                       (r'^mbaliases/edit/(?P<alias_id>\d+)/$', 'editmbalias'),
                       (r'^mbaliases/delete/$', 'delmbalias'),

                       (r'^domains/(?P<dom_id>\d+)/raw/$', 'mailboxes_raw'),
                       #url(r'^domains/(?P<dom_id>\d+)/aliases/$', "aliases", name="full-aliases"),
                       #url(r'^domains/(?P<dom_id>\d+)/aliases/(?P<mbox_id>\d+)/$', "aliases", name="mbox-aliases"),

                       (r'^settings/$', 'viewparameters'),
                       (r'^settings/parameters/$', 'viewparameters'),
                       (r'^settings/parameters/save/$', 'saveparameters'),
                       (r'^settings/extensions/$', 'viewextensions'),
                       (r'^settings/extensions/save/$', 'saveextensions'),

                       (r'^permissions/$', 'permissions'),
                       (r'^permissions/add/$', 'add_permission'),
                       (r'^permissions/delete/$', 'delete_permissions'),
                       )
