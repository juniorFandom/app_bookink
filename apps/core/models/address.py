from django.db import models
from django.utils.translation import gettext_lazy as _
from .base import TimeStampedModel


class Address(TimeStampedModel):
    """
    Model representing a physical address with geolocation support.
    """
    street_address = models.CharField(
        _('Street Address'),
        max_length=255,
        blank=True,
        help_text=_('Street address including house/building number')
    )
    neighborhood = models.CharField(
        _('Neighborhood'),
        max_length=100,
        blank=True,
        help_text=_('Neighborhood or district')
    )
    city = models.CharField(
        _('City'),
        max_length=100,
        help_text=_('City name')
    )
    region = models.CharField(
        _('Region'),
        max_length=100,
        help_text=_('State, province, or region')
    )
    country = models.CharField(
        _('Country'),
        max_length=100,
        default='Cameroon',
        help_text=_('Country name')
    )
    postal_code = models.CharField(
        _('Postal Code'),
        max_length=20,
        blank=True,
        help_text=_('Postal or ZIP code')
    )
    latitude = models.DecimalField(
        _('Latitude'),
        max_digits=10,
        decimal_places=8,
        null=True,
        blank=True,
        help_text=_('Latitude coordinate')
    )
    longitude = models.DecimalField(
        _('Longitude'),
        max_digits=11,
        decimal_places=8,
        null=True,
        blank=True,
        help_text=_('Longitude coordinate')
    )

    class Meta:
        abstract = True
        verbose_name = _('Address')
        verbose_name_plural = _('Addresses')
        ordering = ['city', 'region']
        db_table = 'address'
        indexes = [
            models.Index(fields=['city']),
            models.Index(fields=['region']),
            models.Index(fields=['country']),
        ]

    def __str__(self):
        parts = []
        if self.street_address:
            parts.append(self.street_address)
        if self.neighborhood:
            parts.append(self.neighborhood)
        parts.extend([self.city, self.region, self.country])
        if self.postal_code:
            parts.append(self.postal_code)
        return ', '.join(parts)

    def get_coordinates(self):
        """Returns the coordinates as a tuple (latitude, longitude) if both exist."""
        if self.latitude is not None and self.longitude is not None:
            return (self.latitude, self.longitude)
        return None

    def has_coordinates(self):
        """Checks if the address has valid coordinates."""
        return self.latitude is not None and self.longitude is not None


class PhysicalAddress(Address):
    """
    Concrete model representing a physical address, inheriting from the abstract Address.
    """
    class Meta(Address.Meta):
        abstract = False
        verbose_name = _('Physical Address')
        verbose_name_plural = _('Physical Addresses')
        db_table = 'physical_address' 