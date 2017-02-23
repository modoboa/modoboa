from django.conf import settings
from django.conf.urls import include, url
from django.views.i18n import JavaScriptCatalog

from modoboa.admin.views.user import forward
from modoboa.core.extensions import exts_pool
from modoboa.core import signals as core_signals


urlpatterns = [
    url(r'^jsi18n/$', JavaScriptCatalog.as_view(), name='javascript-catalog'),
    url('', include('modoboa.core.urls', namespace="core")),
    url('^user/forward/', forward, name="user_forward"),
    url('admin/', include('modoboa.admin.urls', namespace="admin")),
    url('relaydomains/',
        include('modoboa.relaydomains.urls', namespace="relaydomains")),
]

urlpatterns += exts_pool.load_all()

extra_routes = core_signals.extra_uprefs_routes.send(sender="urls")
if extra_routes:
    extra_routes = reduce(
        lambda a, b: a + b, [route[1] for route in extra_routes])
    urlpatterns += extra_routes

# API urls
urlpatterns += [
    url("^api/v1/", include("modoboa.urls_api", namespace="external_api")),
    url("^docs/api/", include('rest_framework_swagger.urls')),
]

if 'modoboa.demo' in settings.INSTALLED_APPS:
    urlpatterns += [
        url(r'^demo/', include('modoboa.demo.urls', namespace="demo"))
    ]

if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    from django.conf.urls.static import static
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
