from django.urls import path
from .views import generate_api_key, generate_token_task 

urlpatterns = [
    path('generate-api-key/', generate_api_key, name='generate_api_key'),
    path('trigger-token-task/', generate_token_task, name='trigger_token_task'),

]
