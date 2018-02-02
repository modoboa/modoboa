# -*- coding: utf-8 -*-

"""Core urls."""

from __future__ import unicode_literals

from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.RootDispatchView.as_view(), name="root"),
    url(r'^dashboard/$', views.DashboardView.as_view(), name="dashboard"),

    url(r'^accounts/login/$', views.dologin, name="login"),
    url(r'^accounts/logout/$', views.dologout, name="logout"),

    url(r'^core/$', views.viewsettings, name="index"),
    url(r'^core/parameters/$', views.parameters, name="parameters"),
    url(r'^core/info/$', views.information, name="information"),
    url(r'^core/logs/$', views.logs, name="log_list"),
    url(r'^core/logs/page/$', views.logs_page, name="logs_page"),
    url(r'^core/top_notifications/check/$',
        views.check_top_notifications,
        name="top_notifications_check"),

    url(r'^user/$', views.index, name="user_index"),
    url(r'^user/preferences/$', views.preferences,
        name="user_preferences"),
    url(r'^user/profile/$', views.profile, name="user_profile"),
    url(r'^user/api/$', views.api_access, name="user_api_access"),
]
