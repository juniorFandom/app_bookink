from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views.web import (
    wallet_detail_view,
    deposit_view,
    withdrawal_view,
    transfer_view,
    transaction_list_view,
    transaction_detail_view,
    business_wallet_detail_view
)
from .views.api import (
    UserWalletViewSet,
    BusinessWalletViewSet,
    UserTransactionViewSet,
    BusinessTransactionViewSet
)

app_name = 'wallets'

# Configuration des routes API
router = DefaultRouter()
router.register(r'user-wallets', UserWalletViewSet, basename='user-wallet')
router.register(r'business-wallets', BusinessWalletViewSet, basename='business-wallet')
router.register(r'user-transactions', UserTransactionViewSet, basename='user-transaction')
router.register(r'business-transactions', BusinessTransactionViewSet, basename='business-transaction')

# Routes web
urlpatterns = [
    # Routes principales
    path('', wallet_detail_view, name='wallet_detail'),
    path('business/', business_wallet_detail_view, name='business_wallet_detail'),
    
    # Routes pour les opérations
    path('deposit/', deposit_view, name='deposit'),
    path('withdraw/', withdrawal_view, name='withdraw'),
    path('transfer/', transfer_view, name='transfer'),
    
    # Routes pour les transactions
    path('transactions/', transaction_list_view, name='transaction_list'),
    path('transactions/<int:pk>/', transaction_detail_view, name='transaction_detail'),
    
    # Routes API
    path('api/', include(router.urls)),
] 