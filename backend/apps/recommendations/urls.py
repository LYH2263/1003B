from django.urls import path
from . import views

urlpatterns = [
    path('submit/', views.recommendation_submit, name='recommendation_submit'),
    path('my/', views.my_recommendations, name='my_recommendations'),
    path('manage/', views.recommendation_manage, name='recommendation_manage'),
    path('<int:pk>/audit/<str:action>/', views.recommendation_audit, name='recommendation_audit'),
    path('<int:pk>/to-book/', views.recommendation_to_book, name='recommendation_to_book'),
]
