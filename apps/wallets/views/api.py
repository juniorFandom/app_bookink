from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _

from ..models import UserWallet, BusinessWallet, UserTransaction, BusinessTransaction
from ..serializers import (
    UserWalletSerializer, BusinessWalletSerializer,
    UserTransactionSerializer, BusinessTransactionSerializer,
    DepositSerializer, WithdrawalSerializer, TransferSerializer,
    WalletDetailSerializer, BusinessWalletDetailSerializer,
    WalletStatisticsSerializer, TransactionStatisticsSerializer
)
from ..services.wallet_service import WalletService
from ..services.transaction_service import TransactionService

User = get_user_model()


class UserWalletViewSet(viewsets.ModelViewSet):
    """ViewSet pour les wallets utilisateur."""
    
    serializer_class = UserWalletSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Retourne uniquement le wallet de l'utilisateur connecté."""
        user = self.request.user
        return UserWallet.objects.filter(user=user)
    
    def get_serializer_class(self):
        """Retourne le serializer approprié selon l'action."""
        if self.action == 'retrieve':
            return WalletDetailSerializer
        return UserWalletSerializer
    
    def perform_create(self, serializer):
        """Crée un wallet pour l'utilisateur connecté."""
        serializer.save(user=self.request.user)
    
    @action(detail=True, methods=['post'])
    def deposit(self, request, pk=None):
        """Effectue un dépôt sur le wallet."""
        wallet = self.get_object()
        serializer = DepositSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                transaction = TransactionService.process_deposit(
                    wallet=wallet,
                    amount=serializer.validated_data['amount'],
                    description=serializer.validated_data.get('description', '')
                )
                return Response({
                    'message': _('Deposit completed successfully'),
                    'transaction': UserTransactionSerializer(transaction).data
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({
                    'error': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def withdraw(self, request, pk=None):
        """Effectue un retrait du wallet."""
        wallet = self.get_object()
        serializer = WithdrawalSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                transaction = TransactionService.process_withdrawal(
                    wallet=wallet,
                    amount=serializer.validated_data['amount'],
                    description=serializer.validated_data.get('description', '')
                )
                return Response({
                    'message': _('Withdrawal completed successfully'),
                    'transaction': UserTransactionSerializer(transaction).data
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({
                    'error': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def transfer(self, request, pk=None):
        """Effectue un transfert depuis le wallet."""
        wallet = self.get_object()
        serializer = TransferSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                recipient_wallet = serializer.get_recipient_wallet()
                outgoing_transaction, incoming_transaction = TransactionService.process_transfer(
                    sender_wallet=wallet,
                    recipient_wallet=recipient_wallet,
                    amount=serializer.validated_data['amount'],
                    description=serializer.validated_data.get('description', '')
                )
                return Response({
                    'message': _('Transfer completed successfully'),
                    'outgoing_transaction': UserTransactionSerializer(outgoing_transaction).data,
                    'incoming_transaction': UserTransactionSerializer(incoming_transaction).data
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({
                    'error': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Récupère les statistiques du wallet."""
        wallet = self.get_object()
        wallet_stats = WalletService.get_wallet_statistics(wallet)
        transaction_stats = TransactionService.get_transaction_statistics(wallet)
        
        return Response({
            'wallet_statistics': WalletStatisticsSerializer(wallet_stats).data,
            'transaction_statistics': TransactionStatisticsSerializer(transaction_stats).data
        })
    
    @action(detail=True, methods=['get'])
    def transactions(self, request, pk=None):
        """Récupère les transactions du wallet."""
        wallet = self.get_object()
        transactions = wallet.transactions.all()
        
        # Filtres optionnels
        transaction_type = request.query_params.get('type')
        status_filter = request.query_params.get('status')
        
        if transaction_type:
            transactions = transactions.filter(transaction_type=transaction_type)
        if status_filter:
            transactions = transactions.filter(status=status_filter)
        
        serializer = UserTransactionSerializer(transactions, many=True)
        return Response(serializer.data)


class BusinessWalletViewSet(viewsets.ModelViewSet):
    """ViewSet pour les wallets entreprise."""
    
    serializer_class = BusinessWalletSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Retourne uniquement les wallets des entreprises de l'utilisateur connecté."""
        user = self.request.user
        # Vérifier si l'utilisateur est propriétaire d'une entreprise
        try:
            business = user.business
            return BusinessWallet.objects.filter(business=business)
        except:
            return BusinessWallet.objects.none()
    
    def get_serializer_class(self):
        """Retourne le serializer approprié selon l'action."""
        if self.action == 'retrieve':
            return BusinessWalletDetailSerializer
        return BusinessWalletSerializer
    
    def perform_create(self, serializer):
        """Crée un wallet pour l'entreprise de l'utilisateur connecté."""
        serializer.save(business=self.request.user.business)
    
    @action(detail=True, methods=['post'])
    def deposit(self, request, pk=None):
        """Effectue un dépôt sur le wallet entreprise."""
        wallet = self.get_object()
        serializer = DepositSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                transaction = TransactionService.process_deposit(
                    wallet=wallet,
                    amount=serializer.validated_data['amount'],
                    description=serializer.validated_data.get('description', '')
                )
                return Response({
                    'message': _('Deposit completed successfully'),
                    'transaction': BusinessTransactionSerializer(transaction).data
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({
                    'error': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def withdraw(self, request, pk=None):
        """Effectue un retrait du wallet entreprise."""
        wallet = self.get_object()
        serializer = WithdrawalSerializer(data=request.data)
        
        if serializer.is_valid():
            try:
                transaction = TransactionService.process_withdrawal(
                    wallet=wallet,
                    amount=serializer.validated_data['amount'],
                    description=serializer.validated_data.get('description', '')
                )
                return Response({
                    'message': _('Withdrawal completed successfully'),
                    'transaction': BusinessTransactionSerializer(transaction).data
                }, status=status.HTTP_201_CREATED)
            except Exception as e:
                return Response({
                    'error': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Récupère les statistiques du wallet entreprise."""
        wallet = self.get_object()
        wallet_stats = WalletService.get_wallet_statistics(wallet)
        transaction_stats = TransactionService.get_transaction_statistics(wallet)
        
        return Response({
            'wallet_statistics': WalletStatisticsSerializer(wallet_stats).data,
            'transaction_statistics': TransactionStatisticsSerializer(transaction_stats).data
        })
    
    @action(detail=True, methods=['get'])
    def transactions(self, request, pk=None):
        """Récupère les transactions du wallet entreprise."""
        wallet = self.get_object()
        transactions = wallet.transactions.all()
        
        # Filtres optionnels
        transaction_type = request.query_params.get('type')
        status_filter = request.query_params.get('status')
        
        if transaction_type:
            transactions = transactions.filter(transaction_type=transaction_type)
        if status_filter:
            transactions = transactions.filter(status=status_filter)
        
        serializer = BusinessTransactionSerializer(transactions, many=True)
        return Response(serializer.data)


class UserTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour les transactions utilisateur (lecture seule)."""
    
    serializer_class = UserTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Retourne uniquement les transactions du wallet de l'utilisateur connecté."""
        user = self.request.user
        wallet = WalletService.get_user_wallet(user)
        if not wallet:
            return UserTransaction.objects.none()
        
        return wallet.transactions.all()
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Annule une transaction."""
        transaction = self.get_object()
        
        try:
            cancelled_transaction = TransactionService.cancel_transaction(transaction)
            return Response({
                'message': _('Transaction cancelled successfully'),
                'transaction': UserTransactionSerializer(cancelled_transaction).data
            })
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class BusinessTransactionViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour les transactions entreprise (lecture seule)."""
    
    serializer_class = BusinessTransactionSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        """Retourne uniquement les transactions des wallets entreprise de l'utilisateur connecté."""
        user = self.request.user
        try:
            business = user.business
            wallet = WalletService.get_business_wallet(business)
            if not wallet:
                return BusinessTransaction.objects.none()
            
            return wallet.transactions.all()
        except:
            return BusinessTransaction.objects.none()
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Annule une transaction."""
        transaction = self.get_object()
        
        try:
            cancelled_transaction = TransactionService.cancel_transaction(transaction)
            return Response({
                'message': _('Transaction cancelled successfully'),
                'transaction': BusinessTransactionSerializer(cancelled_transaction).data
            })
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST) 