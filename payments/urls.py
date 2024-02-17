from django.urls import path
from .views import generate_api_key, generate_token_task, get_data 

urlpatterns = [
    # path('generate-api-key/', generate_api_key, name='generate_api_key'),
    path('generate-api-token/', generate_token_task, name='generate_api_token'),
    path('data', get_data, name="data_a")

]
