from django.urls import path
from . import views

urlpatterns = [
    path('manage/', views.reading_room_manage, name='reading_room_manage'),
    path('manage/<int:room_id>/seats/', views.seat_grid_manage, name='seat_grid_manage'),
    
    path('reservation/', views.seat_reservation, name='seat_reservation'),
    path('my-reservations/', views.my_reservations, name='my_reservations'),
    
    path('api/seat-status/', views.api_seat_status, name='api_seat_status'),
    path('api/create-reservation/', views.api_create_reservation, name='api_create_reservation'),
    path('api/cancel-reservation/<int:reservation_id>/', views.api_cancel_reservation, name='api_cancel_reservation'),
]
