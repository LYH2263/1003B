from django.urls import path
from . import views

urlpatterns = [
    path('api/book/<int:book_id>/graph/', views.book_graph_data, name='book_graph_data'),
]
