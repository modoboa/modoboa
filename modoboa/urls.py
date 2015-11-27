from django.conf import settings
from django.conf.urls import patterns, include, url

from modoboa.admin.app_settings import load_admin_settings
from modoboa.core import load_core_settings
from modoboa.core.extensions import exts_pool
from modoboa.lib import parameters, events
from modoboa.limits.app_settings import load_limits_settings
from modoboa.relaydomains.app_settings import load_relaydomains_settings


load_core_settings()
load_admin_settings()
load_limits_settings()
load_relaydomains_settings()

urlpatterns = patterns(
    '',
    url(r'^$', 'modoboa.lib.web_utils.topredirection', name="topredirection"),
    (r'^jsi18n/$', 'django.views.i18n.javascript_catalog',
     {'packages': ('modoboa', ), }),
    ('', include('modoboa.core.urls', namespace="core")),
    ('', include('modoboa.admin.urls', namespace="admin")),
    ('', include('modoboa.relaydomains.urls', namespace="relaydomains")),
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

# API urls
urlpatterns += patterns(
    "",
    ("^api/v1/", include("modoboa.urls_api", namespace="external_api")),
)

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
