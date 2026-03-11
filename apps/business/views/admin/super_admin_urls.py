from django.urls import path
from apps.business.views import admin_views

app_name = 'super_admin'

urlpatterns = [
    # Dashboard principal
    path('dashboard/', admin_views.super_admin_dashboard, name='dashboard'),
    
    # Wallet et commissions
    path('wallet/', admin_views.super_admin_wallet, name='wallet'),
    
    # Gestion des approbations
    path('approvals/', admin_views.business_approval_list, name='approval_list'),
    path('approve/<int:pk>/', admin_views.approve_business_location, name='approve_business'),
    path('reject/<int:pk>/', admin_views.reject_business_location, name='reject_business'),
    
    # API pour les statistiques
    path('api/stats/', admin_views.api_dashboard_stats, name='api_stats'),
] 