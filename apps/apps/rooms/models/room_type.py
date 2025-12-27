from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import TimeStampedModel


class RoomType(TimeStampedModel):
    """
    Model representing different types of rooms (e.g., Single, Double, Suite).
    """
    name = models.CharField(_('Name'), max_length=100, unique=True)
    code = models.CharField(_('Code'), max_length=30, unique=True)
    description = models.TextField(_('Description'), blank=True)
    max_occupancy = models.PositiveIntegerField(_('Maximum occupancy'))
    base_price = models.DecimalField(
        _('Base price'),
        max_digits=10,
        decimal_places=2,
        help_text=_('Base price per night')
    )
    amenities = models.JSONField(
        _('Amenities'),
        null=True,
        blank=True,
        help_text=_('List of amenities included with this room type')
    )
    image = models.ImageField(
        _('Image'),
        upload_to='rooms/room_types/',
        blank=True
    )
    is_active = models.BooleanField(_('Is active'), default=True)

    class Meta:
        verbose_name = _('Room type')
        verbose_name_plural = _('Room types')
        ordering = ['name']

    def __str__(self):
        return self.name 