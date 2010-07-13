from django.conf.urls.defaults import *
from django.conf import settings

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

from modoboa.extensions import *
from modoboa.lib import parameters

urlpatterns = patterns('',
    # Example:
    # (r'^modoboa/', include('modoboa.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/(.*)', admin.site.root),

    (r'^modoboa/admin/', include('modoboa.admin.urls')),
    (r'^modoboa/userprefs/', include('modoboa.userprefs.urls')),
    (r'^accounts/login/$', 'modoboa.auth.views.dologin'),
    (r'^accounts/logout/$', 'modoboa.auth.views.dologout'),
    (r'^jsi18n/$', 'django.views.i18n.javascript_catalog', 
     {'packages': ('modoboa',),}),

    *loadextensions()
)

if settings.DEBUG:
    urlpatterns += patterns(
        '',
        (r'^static/(?P<path>.*)$', 'django.views.static.serve',
         {'document_root': settings.STATIC_ROOTDIR})
        )
    # Stats
    if isenabled('stats'):
        urlpatterns += patterns(
            '',
            (r'^img/stats/(?P<path>.*)/$', 'django.views.static.serve',
             {'document_root': parameters.get_admin("stats", "IMG_ROOTDIR")})
            )


