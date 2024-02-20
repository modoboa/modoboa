"""PDF Credentials API urls."""

from django.urls import path


from . import views

urlpatterns = [
    path(
        "credentials/<int:account_id>/",
        views.PDFCredentialView.as_view(),
        name="get-credentials",
    ),
]
