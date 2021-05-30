from functools import reduce

from ckeditor_uploader import views as cku_views

from django.conf import settings
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.urls import include, path
from django.views.i18n import JavaScriptCatalog

from drf_spectacular.views import (
    SpectacularJSONAPIView, SpectacularSwaggerView, SpectacularRedocView
)

from modoboa.admin.views import user as user_views
from modoboa.core import signals as core_signals, views as core_views
from modoboa.core.extensions import exts_pool

urlpatterns = [
    path('jsi18n/', JavaScriptCatalog.as_view(), name="javascript-catalog"),

    path('ckeditor/upload/', login_required(cku_views.upload),
         name="ckeditor_upload"),
    path('ckeditor/browse/', login_required(cku_views.browse),
         name="ckeditor_browse"),

    path('', include("modoboa.core.urls")),
    path('admin/', include("modoboa.admin.urls")),
    path('dnstools/', include("modoboa.dnstools.urls")),
    path('stats/', include("modoboa.maillog.urls")),

    path('user/forward/', user_views.forward, name="user_forward"),

    path('accounts/password_reset/', core_views.PasswordResetView.as_view(),
         name="password_reset"),
    path('accounts/password_reset/done/',
         auth_views.PasswordResetDoneView.as_view(),
         name="password_reset_done"),
    path('reset/confirm_code/',
         core_views.VerifySMSCodeView.as_view(),
         name="password_reset_confirm_code"),
    path('reset/resend_code/',
         core_views.ResendSMSCodeView.as_view(),
         name="password_reset_resend_code"),
    path('reset/<uidb64>/<token>/',
         auth_views.PasswordResetConfirmView.as_view(),
         name="password_reset_confirm"),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(),
         name="password_reset_complete"),
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
    # FIXME: legacy, to remove ASAP
    path('docs/openapi.json',
         SpectacularJSONAPIView.as_view(api_version="v1"), name='schema-v1-legacy'),

    path('api/schema-v1/',
         SpectacularJSONAPIView.as_view(api_version="v1"), name='schema-v1'),
    path('api/schema-v1/swagger/',
         SpectacularSwaggerView.as_view(url_name='schema-v1'),
         name='docs-index-v1'),
    path('api/schema-v1/redoc/',
         SpectacularRedocView.as_view(url_name='schema-v1')),

    path('api/schema-v2/',
         SpectacularJSONAPIView.as_view(api_version="v2"), name='schema-v2'),
    path('api/schema-v2/swagger/',
         SpectacularSwaggerView.as_view(url_name='schema-v2'),
         name='docs-index-v2'),
    path('api/schema-v2/redoc/',
         SpectacularRedocView.as_view(url_name='schema-v2')),
    path('api/v1/', include("modoboa.urls_api_v1", namespace="v1")),
    path('api/v2/', include("modoboa.urls_api_v2", namespace="v2")),
]

if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    from django.conf.urls.static import static
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
