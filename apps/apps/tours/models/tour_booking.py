from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import Booking
from django.core.validators import MinValueValidator
from .tour_schedule import TourSchedule
from .tour import Tour
from django.contrib.contenttypes.fields import GenericRelation

class TourBooking(Booking):
    """
    Model for tour bookings, inheriting from Booking base class.
    """
    tour = models.ForeignKey(
        Tour,
        on_delete=models.PROTECT,
        related_name='bookings',
        verbose_name=_('Tour')
    )
    tour_schedule = models.ForeignKey(
        TourSchedule,
        on_delete=models.PROTECT,
        related_name='bookings',
        verbose_name=_('Tour Schedule'),
        null=True,
        blank=True
    )
    number_of_participants = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name=_('Number of Participants')
    )
    
    guide_notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Guide Notes')
    )
    
    payment_percentage = models.IntegerField(
        default=100,
        choices=[
            (20, '20% - Acompte'),
            (50, '50% - Demi-paiement'),
            (100, '100% - Paiement complet')
        ],
        verbose_name=_('Payment Percentage')
    )
    
    amount_paid = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        verbose_name=_('Amount Paid')
    )
    
    # Relation vers les transactions
    transactions = GenericRelation(
        'wallets.UserTransaction',
        content_type_field='content_type',
        object_id_field='object_id',
        related_query_name='tour_booking'
    )

    class Meta:
        verbose_name = _('Tour Booking')
        verbose_name_plural = _('Tour Bookings')
        ordering = ['-created_at']

    def __str__(self):
        return f"Tour Booking {self.booking_reference} - {self.customer.get_full_name()}"

    def generate_booking_reference(self):
        """Generate tour booking specific reference"""
        from django.utils.crypto import get_random_string
        return f"TB{get_random_string(8).upper()}"