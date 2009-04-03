from django.conf.urls.defaults import *

urlpatterns = patterns('mailng.admin.views',
                       (r'^$', 'domains'),
                       (r'^domains/$', 'domains'),
                       (r'^domains/new/', 'newdomain'),
                       (r'^domains/(?P<dom_id>\d+)/edit/$', 'editdomain'),
                       (r'^domains/(?P<dom_id>\d+)/delete/$', 'deldomain'),
                       (r'^domains/(?P<dom_id>\d+)/newmailbox/$', 'newmailbox'),
                       (r'^domains/(?P<dom_id>\d+)/editmailbox/(?P<mbox_id>\d+)/$', 'editmailbox'),
                       (r'^domains/(?P<dom_id>\d+)/deletemailbox/(?P<mbox_id>\d+)/$', 'delmailbox'),
                       (r'^domains/(?P<dom_id>\d+)/newalias/(?P<mbox_id>\d+)/$', 'newalias'),
                       (r'^domains/(?P<dom_id>\d+)/editalias/(?P<alias_id>\d+)/$', 'editalias'),
                       (r'^domains/(?P<dom_id>\d+)/$', 'mailboxes'),
                       url(r'^domains/(?P<dom_id>\d+)/aliases/$', "aliases", name="full-aliases"),
                       url(r'^domains/(?P<dom_id>\d+)/aliases/(?P<mbox_id>\d+)/$', "aliases", name="mbox-aliases"),
                       (r'^domains/(?P<dom_id>\d+)/delalias/(?P<alias_id>\d+)/$', 'delalias'),
                       (r'^settings/$', 'settings'),
                       )
