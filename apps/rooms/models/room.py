from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import TimeStampedModel


class Room(TimeStampedModel):
    """
    Model representing individual rooms in a business location.
    """
    business_location = models.ForeignKey(
        'business.BusinessLocation',
        on_delete=models.CASCADE,
        related_name='rooms',
        verbose_name=_('Business location')
    )
    room_type = models.ForeignKey(
        'rooms.RoomType',
        on_delete=models.PROTECT,
        related_name='rooms',
        verbose_name=_('Room type')
    )
    room_number = models.CharField(_('Room number'), max_length=50)
    floor = models.IntegerField(_('Floor'), null=True, blank=True)
    description = models.TextField(_('Description'), blank=True)
    price_per_night = models.DecimalField(
        _('Price per night'),
        max_digits=10,
        decimal_places=2
    )
    max_occupancy = models.PositiveIntegerField(_('Maximum occupancy'))
    amenities = models.JSONField(
        _('Amenities'),
        null=True,
        blank=True,
        help_text=_('Room-specific amenities')
    )
    is_available = models.BooleanField(_('Is available'), default=True)
    maintenance_mode = models.BooleanField(_('Maintenance mode'), default=False)

    class Meta:
        verbose_name = _('Room')
        verbose_name_plural = _('Rooms')
        unique_together = ['business_location', 'room_number']
        ordering = ['room_number']

    def __str__(self):
        return f"{self.business_location.name} - Room {self.room_number}" 