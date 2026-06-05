from django.urls import path
from . import views

urlpatterns = [
    path('sign/<int:pk>/', views.sign_contract, name='sign_contract'),
    path('download/<int:pk>/', views.download_contract, name='download_contract'),
    path('preview/<int:pk>/', views.preview_contract, name='preview_contract'),
]
