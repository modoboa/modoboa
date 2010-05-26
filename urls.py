from django.conf.urls.defaults import *
from django.conf import settings

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

from mailng.extensions import *
from mailng.lib import parameters

urlpatterns = patterns('',
    # Example:
    # (r'^mailng/', include('mailng.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/(.*)', admin.site.root),

    (r'^mailng/admin/', include('mailng.admin.urls')),
    (r'^mailng/userprefs/', include('mailng.userprefs.urls')),
    (r'^accounts/login/$', 'mailng.auth.views.dologin'),
    (r'^accounts/logout/$', 'django.contrib.auth.views.logout_then_login'),
    (r'^jsi18n/$', 'django.views.i18n.javascript_catalog', 
     {'packages': ('mailng',),}),

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
             {'document_root': parameters.get("stats", "IMG_ROOTDIR")})
            )


