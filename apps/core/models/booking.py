from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from apps.core.models import TimeStampedModel
from apps.wallets.models import UserTransaction
from django.contrib.contenttypes.fields import GenericRelation

class Booking(TimeStampedModel):
    """
    Abstract base model for all booking types.
    Contains common fields and functionality shared across different booking types.
    """
    STATUS_CHOICES = [
        ('PENDING', _('Pending')),
        ('CONFIRMED', _('Confirmed')),
        ('CANCELLED', _('Cancelled')),
        ('COMPLETED', _('Completed')),
        ('NO_SHOW', _('No Show'))
    ]

    transactions = GenericRelation(
        UserTransaction,
        content_type_field='content_type',
        object_id_field='object_id',
        related_query_name='booking',
        verbose_name=_('Transactions liées'),
    )
    # Common fields for all bookings
    customer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        verbose_name=_('Customer')
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name=_('Total Amount')
    )
    commission_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name=_('Commission Amount')
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING',
        verbose_name=_('Status')
    )
    booking_reference = models.CharField(
        max_length=50,
        unique=True,
        verbose_name=_('Booking Reference')
    )
    special_requests = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Special Requests')
    )
    customer_notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Customer Notes')
    )
    cancellation_reason = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Cancellation Reason')
    )
    cancelled_at = models.DateTimeField(
        blank=True,
        null=True,
        verbose_name=_('Cancelled At')
    )

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def __str__(self):
        return f"Booking {self.booking_reference}"

    def save(self, *args, **kwargs):
        if not self.booking_reference:
            self.booking_reference = self.generate_booking_reference()
        super().save(*args, **kwargs)

    def generate_booking_reference(self):
        """
        Generate a unique booking reference.
        Should be overridden in child classes for specific prefixes.
        """
        from django.utils.crypto import get_random_string
        return f"BK{get_random_string(8).upper()}"

    def is_cancellable(self):
        """Check if booking can be cancelled"""
        return self.status in ['PENDING', 'CONFIRMED']

    def is_modifiable(self):
        """Check if booking can be modified"""
        return self.status in ['PENDING', 'CONFIRMED']