from django.urls import path
from . import views

urlpatterns = [
    path('submit/', views.donation_submit, name='donation_submit'),
    path('query/', views.donation_query, name='donation_query'),
    path('manage/', views.donation_manage, name='donation_manage'),
    path('manage/<int:pk>/', views.donation_detail, name='donation_detail'),
    path('manage/<int:pk>/audit/<str:action>/', views.donation_audit, name='donation_audit'),
    path('manage/<int:pk>/to-books/', views.donation_to_books, name='donation_to_books'),
    path('manage/<int:pk>/thank-you-pdf/', views.generate_thank_you_pdf, name='thank_you_pdf'),
]
