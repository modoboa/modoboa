"""Sieve urls."""

from django.urls import path

from . import views

app_name = "sievefilters"

urlpatterns = [
    path("", views.index, name="index"),
    path("savefs/<str:name>/", views.savefs, name="fs_save"),
    path("newfs/", views.new_filters_set, name="fs_add"),
    path("removefs/<str:name>/", views.remove_filters_set, name="fs_delete"),
    path("activatefs/<str:name>/", views.activate_filters_set, name="fs_activate"),
    path("downloadfs/<str:name>/", views.download_filters_set, name="fs_download"),
    path("templates/<str:ftype>/", views.get_templates, name="templates_get"),
    path("<str:setname>/newfilter/", views.newfilter, name="filter_add"),
    path(
        "<str:setname>/editfilter/<path:fname>/", views.editfilter, name="filter_change"
    ),
    path(
        "<str:setname>/removefilter/<path:fname>/",
        views.removefilter,
        name="filter_delete",
    ),
    path(
        "<str:setname>/togglestate/<path:fname>/",
        views.toggle_filter_state,
        name="filter_toggle_state",
    ),
    path(
        "<str:setname>/moveup/<path:fname>/",
        views.move_filter_up,
        name="filter_move_up",
    ),
    path(
        "<str:setname>/movedown/<path:fname>/",
        views.move_filter_down,
        name="filter_move_down",
    ),
    path("<str:name>/", views.getfs, name="fs_get"),
]
