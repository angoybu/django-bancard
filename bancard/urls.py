from django.urls import path

from .views import callback_view

urlpatterns = [
    path("callback/", callback_view, name="bancard_callback"),
]
