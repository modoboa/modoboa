"""Transport urls."""

from django.conf.urls import url

from . import views


urlpatterns = [
    url(r"^$", views.TransportListView.as_view(),
        name="transport_list"),
    url("^create/$", views.TransportCreateView.as_view(),
        name="transport_create"),
    url("^update/(?P<pk>\d+)/$", views.TransportUpdateView.as_view(),
        name="transport_update"),
    url("^delete/(?P<pk>\d+)/$", views.TransportDeleteView.as_view(),
        name="transport_delete"),
]
