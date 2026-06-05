from django.urls import path
from . import views

urlpatterns = [
    path('list/', views.get_notifications, name='notification_list'),
    path('<int:pk>/read/', views.mark_as_read, name='notification_read'),
    path('read-all/', views.mark_all_as_read, name='notification_read_all'),
    path('unread-count/', views.get_unread_count, name='notification_unread_count'),
]
