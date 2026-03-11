import uuid
from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string

from ..models import RestaurantOrder, OrderItem, MenuItem
from apps.wallets.models.wallet import UserWallet, BusinessLocationWallet
from apps.wallets.models.transaction import UserTransaction, BusinessTransaction
from apps.users.models import User
from django.utils import timezone
import uuid


def generate_order_number():
    while True:
        order_number = f"ORD{get_random_string(8).upper()}"
        if not RestaurantOrder.objects.filter(order_number=order_number).exists():
            return order_number


class OrderService:
    """Service class for handling order-related business logic."""

    @staticmethod
    def create_order(business_location, customer, order_type, **kwargs):
        """
        Create a new restaurant order.
        
        Args:
            business_location: The business location where the order is placed
            customer: The customer placing the order
            order_type: The type of order (DINE_IN, TAKEAWAY, DELIVERY)
            **kwargs: Additional order details
            
        Returns:
            RestaurantOrder: The created order
        """
        with transaction.atomic():
            # Generate order number
            order_number = OrderService._generate_order_number()
            
            # Create the order
            order = RestaurantOrder.objects.create(
                business_location=business_location,
                customer=customer,
                order_number=order_number,
                order_type=order_type,
                payment_status='PAID',
                **kwargs
            )
            
            return order

    @staticmethod
    def add_order_item(order, menu_item, quantity, **kwargs):
        """
        Add an item to an order.
        
        Args:
            order: The order to add the item to
            menu_item: The menu item to add
            quantity: The quantity of the item
            **kwargs: Additional item details
            
        Returns:
            OrderItem: The created order item
        """
        with transaction.atomic():
            # Validate menu item availability
            if not menu_item.is_available:
                raise ValidationError(_('This menu item is not available.'))
            
            # Décrémenter le stock du menu_item
            if menu_item.stock_quantity is not None:
                if menu_item.stock_quantity < quantity:
                    raise ValidationError(_('Stock insuffisant pour ce plat.'))
                menu_item.stock_quantity -= quantity
                if menu_item.stock_quantity == 0:
                    menu_item.is_available = False
                menu_item.save()
            
            # Create the order item
            order_item = OrderItem.objects.create(
                restaurant_order=order,
                menu_item=menu_item,
                quantity=quantity,
                unit_price=menu_item.price,
                **kwargs
            )
            
            # Update order totals
            order.calculate_total()
            order.save()
            
            return order_item

    @staticmethod
    def update_order_status(order, new_status, **kwargs):
        """
        Update the status of an order.
        
        Args:
            order: The order to update
            new_status: The new status
            **kwargs: Additional status update details
            
        Returns:
            RestaurantOrder: The updated order
        """
        with transaction.atomic():
            # Validate status transition
            if not OrderService._is_valid_status_transition(order.status, new_status):
                raise ValidationError(_('Invalid status transition.'))
            
            # Update order status
            order.status = new_status
            
            # Handle specific status updates
            if new_status == 'CANCELLED':
                order.cancelled_at = timezone.now()
                if 'cancellation_reason' in kwargs:
                    order.cancellation_reason = kwargs['cancellation_reason']
            
            if 'restaurant_notes' in kwargs:
                order.restaurant_notes = kwargs['restaurant_notes']
            
            order.save()
            return order

    @staticmethod
    def update_payment_status(order, new_status):
        """
        Update the payment status of an order.
        
        Args:
            order: The order to update
            new_status: The new payment status
            
        Returns:
            RestaurantOrder: The updated order
        """
        with transaction.atomic():
            # Validate payment status transition
            if not OrderService._is_valid_payment_status_transition(order.payment_status, new_status):
                raise ValidationError(_('Invalid payment status transition.'))
            
            order.payment_status = new_status
            order.save()
            return order

    @staticmethod
    def _generate_order_number():
        """Generate a unique order number."""
        while True:
            order_number = f"ORD{get_random_string(8).upper()}"
            if not RestaurantOrder.objects.filter(order_number=order_number).exists():
                return order_number

    @staticmethod
    def _is_valid_status_transition(current_status, new_status):
        """Check if the status transition is valid."""
        valid_transitions = {
            'PENDING': ['CONFIRMED', 'CANCELLED'],
            'CONFIRMED': ['PREPARING', 'CANCELLED'],
            'PREPARING': ['READY', 'CANCELLED'],
            'READY': ['DELIVERED', 'CANCELLED'],
            'DELIVERED': ['REFUNDED'],
            'CANCELLED': [],
            'REFUNDED': [],
        }
        return new_status in valid_transitions.get(current_status, [])

    @staticmethod
    def _is_valid_payment_status_transition(current_status, new_status):
        """Check if the payment status transition is valid."""
        valid_transitions = {
            'PENDING': ['PAID', 'FAILED'],
            'PAID': ['REFUNDED'],
            'FAILED': ['PENDING'],
            'REFUNDED': [],
        }
        return new_status in valid_transitions.get(current_status, [])

    @classmethod
    @transaction.atomic
    def create_order(cls, business_location, customer, items_data, **kwargs):
        """
        Create a new restaurant order.
        
        Args:
            business_location: BusinessLocation instance
            customer: User instance
            items_data: List of dicts with menu_item_id and quantity
            **kwargs: Additional order data (order_type, table_number, etc.)
        """
        # Validate items data
        if not items_data:
            raise ValidationError(_("Order must contain at least one item"))

        # Create order
        order = RestaurantOrder.objects.create(
            business_location=business_location,
            customer=customer,
            order_number=cls.generate_order_number(),
            payment_status='PAID',
            **kwargs
        )

        # Create order items
        for item_data in items_data:
            menu_item = item_data['menu_item']
            quantity = item_data['quantity']
            
            if not menu_item.is_available:
                raise ValidationError(
                    _("Menu item '%(item)s' is not available") % {'item': menu_item.name}
                )

            # Décrémenter le stock du menu_item
            if menu_item.stock_quantity is not None:
                if menu_item.stock_quantity < quantity:
                    raise ValidationError(_('Stock insuffisant pour ce plat.'))
                menu_item.stock_quantity -= quantity
                if menu_item.stock_quantity == 0:
                    menu_item.is_available = False
                menu_item.save()

            OrderItem.objects.create(
                restaurant_order=order,
                menu_item=menu_item,
                quantity=quantity,
                unit_price=menu_item.price,
                total_price=menu_item.price * quantity,
                special_instructions=item_data.get('special_instructions', '')
            )

        # Calculate commission
        commission_amount = business_location.business.calculate_commission(order.total_amount)
        order.commission_amount = commission_amount
        
        # Calculate net amount for business (total - commission)
        net_amount = order.total_amount - commission_amount
        
        # Get business location wallet
        business_wallet = BusinessLocationWallet.objects.select_for_update().get(business_location=business_location)
        
        # Get super admin wallet (first user or specific admin)
        super_admin = User.objects.filter(is_superuser=True).first()
        if not super_admin:
            super_admin = User.objects.order_by('id').first()
        
        super_admin_wallet = getattr(super_admin, 'wallet', None)
        
        # Credit business location with net amount (total - commission)
        if not business_wallet.deposit(net_amount):
            raise ValidationError(f"Erreur lors du crédit du wallet business pour {business_location.name}.")
        
        # Create transaction for business location
        UserTransaction.objects.create(
            wallet=business_wallet,
            transaction_type='PAYMENT',
            amount=net_amount,
            status='COMPLETED',
            reference=str(uuid.uuid4()),
            description=f"Paiement net reçu pour commande {order.order_number} (après commission)",
            content_object=order,
            created_at=timezone.now()
        )
        
        # Credit super admin with commission
        if commission_amount > 0 and super_admin_wallet:
            if not super_admin_wallet.deposit(commission_amount):
                raise ValidationError("Erreur lors du crédit de la commission au wallet admin.")
            
            # Create commission transaction
            UserTransaction.objects.create(
                wallet=super_admin_wallet,
                transaction_type='COMMISSION',
                amount=commission_amount,
                status='COMPLETED',
                reference=str(uuid.uuid4()),
                description=f"Commission commande {order.order_number} - {business_location.name}",
                content_object=order,
                created_at=timezone.now()
            )
        
        order.save()

        return order

    @classmethod
    def update_order_status(cls, order, new_status, notes=None):
        """
        Update the status of an order.
        
        Args:
            order: RestaurantOrder instance
            new_status: New status value
            notes: Optional notes about the status change
        """
        if new_status not in dict(RestaurantOrder.STATUS_CHOICES):
            raise ValidationError(_("Invalid order status"))

        if new_status == 'CANCELLED' and order.status not in ['PENDING', 'CONFIRMED']:
            raise ValidationError(_("Cannot cancel order in current status"))

        old_status = order.status
        order.status = new_status

        if new_status == 'CANCELLED':
            order.cancelled_at = timezone.now()
            if notes:
                order.cancellation_reason = notes

        if notes:
            order.restaurant_notes = (
                f"{order.restaurant_notes}\n"
                f"{timezone.now()}: Status changed from {old_status} to {new_status}.\n"
                f"Notes: {notes}"
            ).strip()

        order.save()
        return order

    @classmethod
    def update_payment_status(cls, order, new_status):
        """
        Update the payment status of an order.
        
        Args:
            order: RestaurantOrder instance
            new_status: New payment status value
        """
        if new_status not in dict(RestaurantOrder.PAYMENT_STATUS_CHOICES):
            raise ValidationError(_("Invalid payment status"))

        order.payment_status = new_status
        order.save()
        return order 

def validate_cart_checkout(user, cart):
    """
    Valide le panier utilisateur, débite le wallet utilisateur, crédite les wallets business,
    crée les commandes par business location, et trace toutes les transactions.
    Args:
        user: instance de User
        cart: dict {item_id: {name, price, quantity, image, stock_quantity, ...}}
    Returns:
        dict: {'success': bool, 'errors': list, 'orders': list}
    """
    errors = []
    orders = []
    User = get_user_model()
    try:
        # Conversion stricte de tous les prix en Decimal AVANT tout calcul
        cart_decimal = {}
        for item_id, item in cart.items():
            cart_decimal[item_id] = item.copy()
            cart_decimal[item_id]['price'] = Decimal(str(item['price']))
        # 1. Calcul du total
        total = sum(item['price'] * int(item['quantity']) for item in cart_decimal.values())
        if total <= 0:
            return {'success': False, 'errors': ['Panier vide ou montant invalide.'], 'orders': []}
        # 2. Vérification du solde
        user_wallet = UserWallet.objects.select_for_update().get(user=user)
        if not user_wallet.has_sufficient_funds(total):
            return {'success': False, 'errors': ["Solde insuffisant dans le wallet."], 'orders': []}
        # 3. Regroupement par business location
        items_by_location = {}
        for item_id, item in cart_decimal.items():
            menu_item = MenuItem.objects.get(pk=item_id)
            location = menu_item.business_location
            if location.pk not in items_by_location:
                items_by_location[location.pk] = {'location': location, 'items': []}
            menu_item_price = Decimal(str(menu_item.price))
            items_by_location[location.pk]['items'].append((menu_item, int(item['quantity']), menu_item_price))
        # 4. Transaction atomique
        with transaction.atomic():
            # Débit utilisateur
            if not user_wallet.withdraw(total):
                raise ValidationError("Erreur lors du débit du wallet utilisateur.")
            user_tx = UserTransaction.objects.create(
                wallet=user_wallet,
                transaction_type='PAYMENT',
                amount=total,
                status='COMPLETED',
                reference=str(uuid.uuid4()),
                description="Paiement commande groupée du panier.",
                created_at=timezone.now()
            )
            # Pour chaque business location
            for loc_pk, data in items_by_location.items():
                location = data['location']
                loc_items = data['items']
                loc_total = sum(price * qty for _, qty, price in loc_items)
                # Créer la commande (RestaurantOrder)
                order = RestaurantOrder.objects.create(
                    customer=user,
                    business_location=location,
                    total_amount=loc_total,
                    subtotal=loc_total,
                    status='PREPARING',
                    payment_status='PAID',
                    order_number=generate_order_number(),
                )
                for menu_item, qty, price in loc_items:
                    # Déstockage : on décrémente le stock_quantity
                    if menu_item.stock_quantity is not None:
                        if menu_item.stock_quantity < qty:
                            raise ValidationError(f"Stock insuffisant pour {menu_item.name}.")
                        menu_item.stock_quantity -= qty
                        if menu_item.stock_quantity == 0:
                            menu_item.is_available = False
                        menu_item.save()
                    OrderItem.objects.create(
                        restaurant_order=order,
                        menu_item=menu_item,
                        quantity=qty,
                        unit_price=price,
                        total_price=price * int(qty)
                    )
                # Créditer le wallet du business location
                business_wallet = BusinessLocationWallet.objects.select_for_update().get(business_location=location)
                if not business_wallet.deposit(loc_total):
                    raise ValidationError(f"Erreur lors du crédit du wallet pour {location.name}.")
                UserTransaction.objects.create(
                    wallet=business_wallet,
                    transaction_type='PAYMENT',
                    amount=loc_total,
                    status='COMPLETED',
                    reference=str(uuid.uuid4()),
                    description=f"Paiement reçu pour commande {order.pk}.",
                    created_at=timezone.now()
                )
                orders.append(order)
            return {'success': True, 'errors': [], 'orders': orders}
    except Exception as e:
        errors.append(str(e))
        # Rollback automatique par transaction.atomic
        return {'success': False, 'errors': errors, 'orders': []} 