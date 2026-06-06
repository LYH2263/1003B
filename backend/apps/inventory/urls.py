from django.urls import path
from . import views

app_name = 'inventory'

urlpatterns = [
    path('alerts/', views.stock_alert_list, name='stock_alert_list'),
    path('alerts/<int:pk>/resolve/', views.stock_alert_mark_resolved, name='stock_alert_resolve'),
    path('alerts/<int:pk>/ignore/', views.stock_alert_mark_ignored, name='stock_alert_ignore'),
    path('alerts/export-csv/', views.export_purchase_suggestions_csv, name='export_purchase_csv'),
]
