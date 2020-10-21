"""Core urls."""

from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path('', views.RootDispatchView.as_view(), name="root"),
    path('dashboard/', views.DashboardView.as_view(), name="dashboard"),

    path('accounts/login/', views.dologin, name="login"),
    path('accounts/logout/', views.dologout, name="logout"),
    path('accounts/2fa_verify/',
         views.TwoFactorCodeVerifyView.as_view(),
         name='2fa_verify'),

    path('core/', views.viewsettings, name="index"),
    path('core/parameters/', views.parameters, name="parameters"),
    path('core/info/', views.information, name="information"),
    path('core/logs/', views.logs, name="log_list"),
    path('core/logs/page/', views.logs_page, name="logs_page"),
    path('core/top_notifications/check/',
         views.check_top_notifications,
         name="top_notifications_check"),

    path('user/', views.index, name="user_index"),
    path('user/preferences/', views.preferences,
         name="user_preferences"),
    path('user/profile/', views.profile, name="user_profile"),
    path('user/api/', views.api_access, name="user_api_access"),
    path('user/security/', views.security, name="user_security"),
]
