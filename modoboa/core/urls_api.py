"""Core API urls."""

from django.conf.urls import patterns, url

from . import api


urlpatterns = patterns(
    "",
    url("^users/(?P<pk>.+)/password/$",
        api.UserPasswordChangeAPIView.as_view(),
        name="user_password_change"),

)
