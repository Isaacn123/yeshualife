from django.urls import path

from . import views

urlpatterns = [
    path("contact/submit/", views.contact_submit, name="contact_submit"),
]
