from decimal import Decimal
from django.utils import timezone
from django.core.exceptions import ValidationError
from apps.wallets.models.wallet import BusinessLocationWallet, UserWallet
from apps.wallets.models.transaction import UserTransaction
from apps.users.models import User
import uuid


class CommissionService:
    """
    Service centralisé pour gérer les commissions sur toutes les transactions
    """
    
    @staticmethod
    def calculate_commission(business_location, amount):
        """
        Calcule le montant de commission pour une transaction donnée
        """
        return business_location.business.calculate_commission(amount)
    
    @staticmethod
    def process_commission_payment(business_location, amount, booking_object, transaction_type='PAYMENT'):
        """
        Traite le paiement avec commission pour une réservation
        
        Args:
            business_location: BusinessLocation instance
            amount: Montant total de la transaction
            booking_object: Objet de réservation (RoomBooking, VehicleBooking, etc.)
            transaction_type: Type de transaction (PAYMENT, REFUND, etc.)
        
        Returns:
            dict: {'success': bool, 'commission_amount': Decimal, 'net_amount': Decimal, 'error': str}
        """
        try:
            # Calculer la commission
            commission_amount = business_location.business.calculate_commission(amount)
            net_amount = amount - commission_amount
            
            # Mettre à jour l'objet de réservation
            booking_object.commission_amount = commission_amount
            booking_object.save()
            
            # Obtenir le wallet business location
            business_wallet = BusinessLocationWallet.objects.select_for_update().get(
                business_location=business_location
            )
            
            # Obtenir le wallet super admin
            super_admin = User.objects.filter(is_superuser=True).first()
            if not super_admin:
                super_admin = User.objects.order_by('id').first()
            
            super_admin_wallet = getattr(super_admin, 'wallet', None)
            
            # Créditer le business location avec le montant net
            if not business_wallet.deposit(net_amount):
                raise ValidationError(f"Erreur lors du crédit du wallet business pour {business_location.name}.")
            
            # Créer la transaction pour le business location
            business_transaction = UserTransaction.objects.create(
                wallet=business_wallet,
                transaction_type=transaction_type,
                amount=net_amount,
                status='COMPLETED',
                reference=str(uuid.uuid4()),
                description=f"Paiement net reçu (après commission {commission_amount:.0f} XAF)",
                content_object=booking_object,
                created_at=timezone.now()
            )
            
            # Créditer le super admin avec la commission
            if commission_amount > 0 and super_admin_wallet:
                if not super_admin_wallet.deposit(commission_amount):
                    raise ValidationError("Erreur lors du crédit de la commission au wallet admin.")
                
                # Créer la transaction de commission
                UserTransaction.objects.create(
                    wallet=super_admin_wallet,
                    transaction_type='COMMISSION',
                    amount=commission_amount,
                    status='COMPLETED',
                    reference=str(uuid.uuid4()),
                    description=f"Commission {business_location.name}",
                    content_object=booking_object,
                    created_at=timezone.now()
                )
            
            return {
                'success': True,
                'commission_amount': commission_amount,
                'net_amount': net_amount,
                'business_transaction': business_transaction
            }
            
        except Exception as e:
            return {
                'success': False,
                'commission_amount': Decimal('0'),
                'net_amount': amount,
                'error': str(e)
            }
    
    @staticmethod
    def process_cancellation_commission(booking, refund_amount):
        """
        Traite les commissions lors d'une annulation
        
        Args:
            booking: Objet de réservation
            refund_amount: Montant à rembourser
        
        Returns:
            dict: {'success': bool, 'commission_business': Decimal, 'commission_admin': Decimal, 'refund_amount': Decimal}
        """
        try:
            # Calculer les commissions d'annulation (9% business + 1% admin)
            commission_business = refund_amount * Decimal('0.09')
            commission_admin = refund_amount * Decimal('0.01')
            final_refund = refund_amount - commission_business - commission_admin
            
            # Obtenir les wallets
            business_location_wallet = getattr(booking.business_location, 'wallet', None)
            
            super_admin = User.objects.filter(is_superuser=True).first()
            if not super_admin:
                super_admin = User.objects.order_by('id').first()
            super_admin_wallet = getattr(super_admin, 'wallet', None)
            
            # Créditer le business location avec sa commission
            if commission_business > 0 and business_location_wallet:
                business_location_wallet.deposit(commission_business)
                UserTransaction.objects.create(
                    wallet=business_location_wallet,
                    transaction_type='COMMISSION',
                    amount=commission_business,
                    status='COMPLETED',
                    description=f"Commission annulation {booking.booking_reference}",
                    content_object=booking,
                    reference=f"COM-BUSINESSLOC-{booking.booking_reference}-{uuid.uuid4().hex[:8]}"
                )
            
            # Créditer le super admin avec sa commission
            if commission_admin > 0 and super_admin_wallet:
                super_admin_wallet.deposit(commission_admin)
                UserTransaction.objects.create(
                    wallet=super_admin_wallet,
                    transaction_type='COMMISSION',
                    amount=commission_admin,
                    status='COMPLETED',
                    description=f"Commission admin annulation {booking.booking_reference}",
                    content_object=booking,
                    reference=f"COM-ADMIN-{booking.booking_reference}-{uuid.uuid4().hex[:8]}"
                )
            
            return {
                'success': True,
                'commission_business': commission_business,
                'commission_admin': commission_admin,
                'refund_amount': final_refund
            }
            
        except Exception as e:
            return {
                'success': False,
                'commission_business': Decimal('0'),
                'commission_admin': Decimal('0'),
                'refund_amount': refund_amount,
                'error': str(e)
            }
    
    @staticmethod
    def get_commission_statistics(start_date=None, end_date=None):
        """
        Obtient les statistiques des commissions
        
        Args:
            start_date: Date de début (optionnel)
            end_date: Date de fin (optionnel)
        
        Returns:
            dict: Statistiques des commissions
        """
        commission_transactions = UserTransaction.objects.filter(
            transaction_type='COMMISSION',
            status='COMPLETED'
        )
        
        if start_date:
            commission_transactions = commission_transactions.filter(created_at__gte=start_date)
        
        if end_date:
            commission_transactions = commission_transactions.filter(created_at__lte=end_date)
        
        from django.db.models import Sum
        total_commission = commission_transactions.aggregate(
            total=Sum('amount')
        )['total'] or Decimal('0')
        
        monthly_commission = commission_transactions.filter(
            created_at__gte=timezone.now().replace(day=1)
        ).aggregate(total=Sum('amount'))['total'] or Decimal('0')
        
        return {
            'total_commission': total_commission,
            'monthly_commission': monthly_commission,
            'transaction_count': commission_transactions.count()
        } 