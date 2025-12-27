from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.core.models import Booking
from .vehicle import Vehicle
from .driver import Driver

class VehicleBooking(Booking):
    """
    Model representing a vehicle booking transaction.
    """
    STATUS_CHOICES = Booking.STATUS_CHOICES + [
        ('PICKED_UP', _('Picked Up')),
        ('RETURNED', _('Returned')),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('UNPAID', _('Unpaid')),
        ('PARTIALLY_PAID', _('Partially Paid')),
        ('PAID', _('Paid')),
        ('REFUNDED', _('Refunded')),
    ]

    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.PROTECT,
        related_name='bookings',
        verbose_name=_('Vehicle')
    )
    driver = models.ForeignKey(
        Driver,
        on_delete=models.PROTECT,
        related_name='vehicle_bookings',
        null=True,
        blank=True,
        verbose_name=_('Driver')
    )
    pickup_datetime = models.DateTimeField(
        _('Pickup Date and Time')
    )
    return_datetime = models.DateTimeField(
        _('Return Date and Time')
    )
    pickup_location = models.CharField(
        _('Pickup Location'),
        max_length=255
    )
    return_location = models.CharField(
        _('Return Location'),
        max_length=255
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
        default='UNPAID'
    )
    daily_rate = models.DecimalField(
        _('Daily Rate'),
        max_digits=10,
        decimal_places=2
    )
    total_days = models.IntegerField(
        _('Total Days'),
        help_text=_('Number of days for the booking')
    )
    subtotal = models.DecimalField(
        _('Subtotal'),
        max_digits=10,
        decimal_places=2,
        help_text=_('Daily rate × Total days')
    )
    driver_fee = models.DecimalField(
        _('Driver Fee'),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    additional_charges = models.DecimalField(
        _('Additional Charges'),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    total_amount = models.DecimalField(
        _('Total Amount'),
        max_digits=10,
        decimal_places=2
    )
    amount_paid = models.DecimalField(
        _('Amount Paid'),
        max_digits=10,
        decimal_places=2,
        default=0
    )
    start_mileage = models.IntegerField(
        _('Start Mileage'),
        null=True,
        blank=True
    )
    end_mileage = models.IntegerField(
        _('End Mileage'),
        null=True,
        blank=True
    )
    notes = models.TextField(
        _('Notes'),
        blank=True
    )
    terms_accepted = models.BooleanField(
        _('Terms Accepted'),
        default=False
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
        verbose_name = _('Vehicle Booking')
        verbose_name_plural = _('Vehicle Bookings')
        ordering = ['-created_at']
        db_table = 'vehicle_booking'

    def __str__(self):
        return f"Vehicle Booking {self.booking_reference} - {self.vehicle}"

    def generate_booking_reference(self):
        """Generate vehicle booking specific reference"""
        from django.utils.crypto import get_random_string
        return f"VB{get_random_string(8).upper()}"

    @property
    def balance_due(self):
        """Calculate the remaining balance to be paid"""
        return self.total_amount - self.amount_paid

    def clean(self):
        """Validate the booking dates and vehicle availability."""
        if self.pickup_datetime and self.return_datetime:
            if self.pickup_datetime >= self.return_datetime:
                raise ValidationError({
                    'return_datetime': _('Return datetime must be after pickup datetime.')
                })
            
            if self.pickup_datetime < timezone.now():
                raise ValidationError({
                    'pickup_datetime': _('Pickup datetime cannot be in the past.')
                })

            # Check vehicle availability for the selected dates
            overlapping_bookings = VehicleBooking.objects.filter(
                vehicle=self.vehicle,
                status__in=['PENDING', 'CONFIRMED', 'PICKED_UP'],
                pickup_datetime__lt=self.return_datetime,
                return_datetime__gt=self.pickup_datetime
            ).exclude(pk=self.pk)

            if overlapping_bookings.exists():
                raise ValidationError(
                    _('Vehicle is not available for the selected dates.')
                )

    def save(self, *args, **kwargs):
        """Calculate booking amounts before saving."""
        if self.pickup_datetime and self.return_datetime:
            # Calculate total days
            delta = self.return_datetime - self.pickup_datetime
            self.total_days = delta.days + 1

            # Calculate amounts
            self.subtotal = self.daily_rate * self.total_days
            self.total_amount = (
                self.subtotal +
                self.driver_fee +
                self.additional_charges
            )

            # Update payment status based on amount paid
            if self.amount_paid == 0:
                self.payment_status = 'UNPAID'
            elif self.amount_paid < self.total_amount:
                self.payment_status = 'PARTIALLY_PAID'
            elif self.amount_paid >= self.total_amount:
                self.payment_status = 'PAID'

        super().save(*args, **kwargs)

    def start_booking(self):
        """Start the booking if confirmed."""
        if self.status == 'CONFIRMED':
            self.status = 'PICKED_UP'
            self.start_mileage = self.vehicle.mileage
            self.save()

    def complete_booking(self, end_mileage):
        """Complete the booking and update vehicle mileage."""
        if self.status == 'PICKED_UP':
            self.status = 'RETURNED'
            self.end_mileage = end_mileage
            self.save()
            
            # Update vehicle mileage
            self.vehicle.update_mileage(end_mileage)

    def cancel_booking(self):
        """Cancel the booking if not already active."""
        if self.status in ['PENDING', 'CONFIRMED']:
            self.status = 'CANCELLED'
            self.save() 