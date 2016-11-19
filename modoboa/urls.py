from django.conf import settings
from django.conf.urls import patterns, include, url

from modoboa.core.extensions import exts_pool
from modoboa.core import signals as core_signals


urlpatterns = patterns(
    '',
    (r'^jsi18n/$', 'django.views.i18n.javascript_catalog',
     {'packages': ('modoboa', ), }),
    ('', include('modoboa.core.urls', namespace="core")),
    url('^user/forward/', 'modoboa.admin.views.user.forward',
        name='user_forward'),
    ('admin/', include('modoboa.admin.urls', namespace="admin")),
    ('relaydomains/',
     include('modoboa.relaydomains.urls', namespace="relaydomains")),
)

urlpatterns += patterns(
    '',
    *exts_pool.load_all()
)

extra_routes = core_signals.extra_uprefs_routes.send(sender="urls")
if extra_routes:
    extra_routes = reduce(
        lambda a, b: a + b, [route for route in extra_routes])
    urlpatterns += patterns(
        '',
        *extra_routes
    )

# API urls
urlpatterns += patterns(
    "",
    ("^api/v1/", include("modoboa.urls_api", namespace="external_api")),
    url("^docs/api/", include('rest_framework_swagger.urls')),
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
