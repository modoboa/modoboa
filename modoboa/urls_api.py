"""External API urls."""

from django.urls import include, path

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from modoboa.core.extensions import exts_pool

app_name = "api"

urlpatterns = [
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(),
         name='token_refresh'),
    path('', include("modoboa.core.urls_api")),
    path('', include("modoboa.admin.urls_api")),
    path('', include("modoboa.parameters.urls_api")),
    path('', include("modoboa.limits.urls_api")),
    path('', include("modoboa.relaydomains.urls_api")),
    path('', include("modoboa.dnstools.urls_api")),
]

urlpatterns += exts_pool.get_urls(category="api")
