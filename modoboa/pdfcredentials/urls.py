from django.urls import path

from . import views

app_name = "pdfcredentials"

urlpatterns = [
    path(
        "credentials/<int:accountid>/",
        views.get_account_credentials,
        name="account_credentials",
    ),
]
