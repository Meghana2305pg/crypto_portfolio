from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('transactions/', views.transactions_view, name='transactions'),
    path('transactions/export_csv/', views.export_transactions_csv, name='export_transactions_csv'),
    path('alerts/', views.price_alerts_view, name='price_alerts'),

    # ✅ FIXED — use the correct view name
    path('asset/<int:asset_id>/chart/', views.asset_chart, name='asset_chart'),

    path('profile/', views.profile, name='profile'),
    path('alerts/create/', views.create_price_alert, name='create_price_alert'),
]