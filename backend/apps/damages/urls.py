from django.urls import path
from . import views

app_name = 'damages'

urlpatterns = [
    path('manage/', views.damage_manage, name='damage_manage'),
    path('report/<int:loan_id>/', views.damage_report_create, name='damage_report_create'),
    path('<int:pk>/', views.damage_detail, name='damage_detail'),
    path('<int:pk>/assess/', views.damage_assess, name='damage_assess'),
    path('<int:pk>/compensate/', views.damage_compensate, name='damage_compensate'),
    path('<int:pk>/waive/', views.damage_waive, name='damage_waive'),
]
