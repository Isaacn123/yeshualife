from django.urls import path

from . import views

app_name = "blog"

urlpatterns = [
    path("events/<slug:slug>/", views.homepage_event_detail, name="homepage_event_detail"),
]
