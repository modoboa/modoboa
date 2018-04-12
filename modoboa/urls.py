# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from functools import reduce

from ckeditor_uploader import views as cku_views

from django.conf import settings
from django.conf.urls import include, url
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from django.views.i18n import JavaScriptCatalog

from rest_framework.documentation import include_docs_urls

from modoboa.admin.views.user import forward
from modoboa.core import signals as core_signals, views as core_views
from modoboa.core.extensions import exts_pool

API_TITLE = "Modoboa API"

urlpatterns = [
    url(r'^jsi18n/$', JavaScriptCatalog.as_view(), name="javascript-catalog"),
    url(r'^ckeditor/upload/', login_required(cku_views.upload),
        name="ckeditor_upload"),
    url(r'^ckeditor/browse/', login_required(cku_views.browse),
        name="ckeditor_browse"),
    url("", include("modoboa.core.urls", namespace="core")),
    url("^user/forward/", forward, name="user_forward"),
    url("admin/", include("modoboa.admin.urls", namespace="admin")),
    # No namespace
    url(r'^accounts/password_reset/$', core_views.password_reset,
        name="password_reset"),
    url(r'^accounts/password_reset/done/$', auth_views.password_reset_done,
        name="password_reset_done"),
    url(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',  # noqa
        auth_views.password_reset_confirm, name="password_reset_confirm"),
    url(r'^reset/done/$', auth_views.password_reset_complete,
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
    url("^docs/api/", include_docs_urls(title=API_TITLE, public=False)),
    url("^api/v1/", include("modoboa.urls_api", namespace="api")),
]

if settings.DEBUG:
    from django.contrib.staticfiles.urls import staticfiles_urlpatterns
    from django.conf.urls.static import static
    urlpatterns += staticfiles_urlpatterns()
    urlpatterns += static(
        settings.MEDIA_URL, document_root=settings.MEDIA_ROOT
    )
