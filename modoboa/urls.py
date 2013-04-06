from django.conf.urls import patterns, include, url
from django.conf import settings
from modoboa.extensions import *
from modoboa.lib import parameters

urlpatterns = patterns('',
    (r'^$', 'modoboa.lib.webutils.topredirection'),
    (r'^admin/', include('modoboa.admin.urls')),
    (r'^accounts/login/$', 'modoboa.auth.views.dologin'),
    (r'^accounts/logout/$', 'modoboa.auth.views.dologout'),
    (r'^jsi18n/$', 'django.views.i18n.javascript_catalog',
     {'packages': ('modoboa', ), }),
    *exts_pool.load_all()
)

if 'modoboa.demo' in settings.INSTALLED_APPS:
    urlpatterns += patterns('',
        (r'^demo/', include('modoboa.demo.urls'))
    )

if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    from django.conf.urls.static import static
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
