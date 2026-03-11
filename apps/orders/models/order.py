from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from apps.business.models import BusinessLocation
from apps.core.models import PhysicalAddress
from decimal import Decimal


class RestaurantOrder(models.Model):
    """
    Model representing a restaurant order.
    """
    ORDER_TYPE_CHOICES = [
        ('DINE_IN', _('Dine In')),
        ('TAKEAWAY', _('Takeaway')),
        ('DELIVERY', _('Delivery')),
    ]

    STATUS_CHOICES = [
        ('PENDING', _('Pending')),
        ('CONFIRMED', _('Confirmed')),
        ('PREPARING', _('Preparing')),
        ('READY', _('Ready')),
        ('DELIVERED', _('Delivered')),
        ('CANCELLED', _('Cancelled')),
        ('REFUNDED', _('Refunded')),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('PENDING', _('Pending')),
        ('PAID', _('Paid')),
        ('REFUNDED', _('Refunded')),
        ('FAILED', _('Failed')),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('CASH', _('Espèces')),
        ('WALLET', _('Portefeuille')),
        ('MOBILE_MONEY', _('Mobile Money')),
        ('CARD', _('Carte bancaire')),
    ]

    business_location = models.ForeignKey(
        BusinessLocation,
        on_delete=models.PROTECT,
        related_name='restaurant_orders_from_location',
        verbose_name=_('Business Location')
    )
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='restaurant_orders',
        verbose_name=_('Customer')
    )
    order_number = models.CharField(
        _('Order Number'),
        max_length=50,
        unique=True,
        help_text=_('Unique order reference number')
    )
    order_type = models.CharField(
        _('Order Type'),
        max_length=20,
        choices=ORDER_TYPE_CHOICES,
        default='DINE_IN'
    )
    table_number = models.CharField(
        _('Table Number'),
        max_length=20,
        blank=True,
        null=True,
        help_text=_('Table number for dine-in orders')
    )
    delivery_address = models.ForeignKey(
        PhysicalAddress,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='restaurant_orders',
        verbose_name=_('Delivery Address')
    )
    subtotal = models.DecimalField(
        _('Subtotal'),
        max_digits=10,
        decimal_places=2,
        help_text=_('Order subtotal before tax and fees')
    )
    tax_amount = models.DecimalField(
        _('Tax Amount'),
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    delivery_fee = models.DecimalField(
        _('Delivery Fee'),
        max_digits=10,
        decimal_places=2,
        default=0.00
    )
    total_amount = models.DecimalField(
        _('Total Amount'),
        max_digits=10,
        decimal_places=2,
        help_text=_('Final order amount including tax and fees')
    )
    commission_amount = models.DecimalField(
        _('Commission Amount'),
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text=_('Platform commission on the order')
    )
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    payment_status = models.CharField(
        _('Payment Status'),
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='PENDING'
    )
    payment_method = models.CharField(
        _('Mode de paiement'),
        max_length=20,
        choices=PAYMENT_METHOD_CHOICES,
        default='CASH',
        help_text=_('Mode de paiement utilisé pour la commande')
    )
    estimated_preparation_time = models.IntegerField(
        _('Estimated Preparation Time'),
        null=True,
        blank=True,
        help_text=_('Estimated preparation time in minutes')
    )
    special_instructions = models.TextField(
        _('Special Instructions'),
        blank=True,
        help_text=_('Special instructions for the entire order')
    )
    customer_notes = models.TextField(
        _('Customer Notes'),
        blank=True
    )
    restaurant_notes = models.TextField(
        _('Restaurant Notes'),
        blank=True
    )
    cancellation_reason = models.TextField(
        _('Cancellation Reason'),
        blank=True
    )
    cancelled_at = models.DateTimeField(
        _('Cancelled At'),
        null=True,
        blank=True
    )
    created_at = models.DateTimeField(
        _('Created At'),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _('Updated At'),
        auto_now=True
    )

    class Meta:
        verbose_name = _('Restaurant Order')
        verbose_name_plural = _('Restaurant Orders')
        ordering = ['-created_at']
        db_table = 'restaurant_order'

    def __str__(self):
        return f"Order {self.order_number} - {self.business_location}"

    def calculate_total(self):
        """Calculate the total amount including tax and fees."""
        self.subtotal = sum(Decimal(item.total_price) for item in self.items.all())
        self.tax_amount = Decimal(self.tax_amount)
        self.delivery_fee = Decimal(self.delivery_fee)
        self.total_amount = self.subtotal + self.tax_amount + self.delivery_fee
        return self.total_amount


class OrderItem(models.Model):
    """
    Model representing an item in a restaurant order.
    """
    restaurant_order = models.ForeignKey(
        RestaurantOrder,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name=_('Restaurant Order')
    )
    menu_item = models.ForeignKey(
        'orders.MenuItem',
        on_delete=models.PROTECT,
        related_name='order_items',
        verbose_name=_('Menu Item')
    )
    quantity = models.IntegerField(
        _('Quantity'),
        help_text=_('Number of items ordered')
    )
    unit_price = models.DecimalField(
        _('Unit Price'),
        max_digits=10,
        decimal_places=2,
        help_text=_('Price per item at the time of order')
    )
    total_price = models.DecimalField(
        _('Total Price'),
        max_digits=10,
        decimal_places=2,
        help_text=_('Total price for this item (quantity × unit price)')
    )
    special_instructions = models.TextField(
        _('Special Instructions'),
        blank=True,
        help_text=_('Special instructions for this item')
    )
    created_at = models.DateTimeField(
        _('Created At'),
        auto_now_add=True
    )

    class Meta:
        verbose_name = _('Order Item')
        verbose_name_plural = _('Order Items')
        ordering = ['created_at']
        db_table = 'order_item'

    def __str__(self):
        return f"{self.quantity}x {self.menu_item.name}"

    def save(self, *args, **kwargs):
        """Calculate total price before saving."""
        self.total_price = self.quantity * self.unit_price
        super().save(*args, **kwargs)
        # Update order total
        self.restaurant_order.calculate_total()
        self.restaurant_order.save() 