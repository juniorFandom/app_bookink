from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import Booking
from apps.rooms.models import Room
from apps.business.models import BusinessLocation


class RoomBooking(Booking):
    """
    Model for room bookings, inheriting from Booking base class.
    """
    STATUS_CHOICES = Booking.STATUS_CHOICES + [
        ('CHECKED_IN', _('Checked In')),
        ('CHECKED_OUT', _('Checked Out')),
    ]

    room = models.ForeignKey(
        Room,
        on_delete=models.PROTECT,
        related_name='bookings',
        verbose_name=_('Room')
    )
    
    business_location = models.ForeignKey(
        BusinessLocation,
        on_delete=models.PROTECT,
        related_name='room_bookings',
        verbose_name=_('Business Location')
    )
    
    check_in_date = models.DateField(_('Check-in Date'))
    check_out_date = models.DateField(_('Check-out Date'))
    adults_count = models.PositiveIntegerField(_('Number of Adults'), default=1)
    children_count = models.PositiveIntegerField(_('Number of Children'), default=0)
    hotel_notes = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Hotel Notes')
    )

    class Meta:
        verbose_name = _('Room Booking')
        verbose_name_plural = _('Room Bookings')
        ordering = ['-created_at']
        unique_together = ['room', 'check_in_date']

    def __str__(self):
        return f"Room Booking {self.booking_reference} - {self.room}"

    def generate_booking_reference(self):
        """Generate room booking specific reference"""
        from django.utils.crypto import get_random_string
        return f"RB{get_random_string(8).upper()}"

    @property
    def duration_nights(self) -> int:
        """Calculate number of nights"""
        return (self.check_out_date - self.check_in_date).days