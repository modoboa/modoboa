from django.conf.urls.defaults import *
from django.conf import settings
from modoboa.extensions import *
from modoboa.lib import parameters

urlpatterns = patterns('',
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
         {'document_root': settings.MEDIA_ROOT})
        )
    # Stats
    if isenabled('stats'):
        urlpatterns += patterns(
            '',
            (r'^img/stats/(?P<path>.*)/$', 'django.views.static.serve',
             {'document_root': parameters.get_admin("stats", "IMG_ROOTDIR")})
            )


