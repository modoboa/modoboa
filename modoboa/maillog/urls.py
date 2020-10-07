"""Stats urls."""

from django.urls import path

from . import views

app_name = "maillog"

urlpatterns = [
    path("", views.index, name="fullindex"),
    path("graphs/", views.graphs, name="graph_list"),
    path("domains/", views.get_domain_list, name="domain_list"),
]
