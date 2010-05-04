from django.conf.urls.defaults import *
from django.conf import settings

# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

from mailng.extensions import loadextensions, loadmenus, isenabled
from mailng.lib import parameters
loadextensions()

urlpatterns = patterns('',
    # Example:
    # (r'^mailng/', include('mailng.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # (r'^admin/(.*)', admin.site.root),

    (r'^mailng/admin/', include('mailng.admin.urls')),
    (r'^mailng/main/', include('mailng.main.urls')),
    (r'^accounts/login/$', 'mailng.auth.views.dologin'),
    (r'^accounts/logout/$', 'django.contrib.auth.views.logout_then_login'),
    (r'^jsi18n/$', 'django.views.i18n.javascript_catalog', 
     {'packages': ('mailng',),})
)

menus = loadmenus()
if menus != ():
    urlpatterns += patterns('', *menus)

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


