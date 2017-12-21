"""Transport urls."""

from django.conf.urls import url

from . import views


urlpatterns = [
    url(r"^$", views.TransportListView.as_view(),
        name="transport_list"),
    url(r"^create/$", views.TransportCreateView.as_view(),
        name="transport_create"),
    url(r"^update/(?P<pk>\d+)/$", views.TransportUpdateView.as_view(),
        name="transport_update"),
    url(r"^delete/(?P<pk>\d+)/$", views.TransportDeleteView.as_view(),
        name="transport_delete"),
]
