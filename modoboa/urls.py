from django.conf import settings
from django.conf.urls import include, url
from django.views.i18n import JavaScriptCatalog

from django.contrib.auth.decorators import login_required

from ckeditor_uploader import views as cku_views
from rest_framework.documentation import include_docs_urls

from modoboa.admin.views.user import forward
from modoboa.core.extensions import exts_pool
from modoboa.core import signals as core_signals

API_TITLE = 'Modoboa API'

urlpatterns = [
    url(r'^jsi18n/$', JavaScriptCatalog.as_view(), name='javascript-catalog'),
    url(r'^ckeditor/upload/', login_required(cku_views.upload),
        name="ckeditor_upload"),
    url(r'^ckeditor/browse/', login_required(cku_views.browse),
        name="ckeditor_browse"),
    url('', include('modoboa.core.urls', namespace="core")),
    url('^user/forward/', forward, name="user_forward"),
    url('admin/', include('modoboa.admin.urls', namespace="admin")),
    url('relaydomains/',
        include('modoboa.relaydomains.urls', namespace="relaydomains")),
]

exts_pool.load_all()
urlpatterns += exts_pool.get_urls()

extra_routes = core_signals.extra_uprefs_routes.send(sender="urls")
if extra_routes:
    extra_routes = reduce(
        lambda a, b: a + b, [route[1] for route in extra_routes])
    urlpatterns += extra_routes

# API urls
urlpatterns += [
    url("^docs/api/", include_docs_urls(title=API_TITLE)),
    url("^api/v1/", include("modoboa.urls_api", namespace="api")),
]

if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    from django.conf.urls.static import static
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
