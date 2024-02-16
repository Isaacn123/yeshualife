from django.urls import path
from .views import generate_api_key 

urlpatterns = [
    path('generate-api-key/', generate_api_key, name='generate_api_key')
]
