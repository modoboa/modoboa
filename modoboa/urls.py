from django.conf import settings
from django.conf.urls import patterns, include, url

from modoboa.core import load_core_settings
from modoboa.core.extensions import exts_pool
from modoboa.lib import parameters, events


load_core_settings()

urlpatterns = patterns(
    '',
    url(r'^$', 'modoboa.lib.web_utils.topredirection', name="topredirection"),
    (r'^jsi18n/$', 'django.views.i18n.javascript_catalog',
     {'packages': ('modoboa', ), }),
    ('', include('modoboa.core.urls', namespace="core")),
)

urlpatterns += patterns(
    '',
    *exts_pool.load_all()
)

urlpatterns += patterns(
    '',
    *events.raiseQueryEvent("ExtraUprefsRoutes")
)

parameters.apply_to_django_settings()

if 'modoboa.demo' in settings.INSTALLED_APPS:
    urlpatterns += patterns(
        '',
        (r'^demo/', include('modoboa.demo.urls', namespace="demo"))
    )

if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    from django.conf.urls.static import static
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
