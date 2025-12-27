from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import TimeStampedModel

class VehicleCategory(TimeStampedModel):
    """
    Model representing a vehicle category (e.g., Sedan, SUV, Van).
    """
    name = models.CharField(
        _('Name'),
        max_length=100,
        unique=True,
        help_text=_('Category name (e.g. Sedan, SUV, Van)')
    )
    code = models.CharField(
        _('Code'),
        max_length=20,
        unique=True,
        help_text=_('Unique code for the category')
    )
    description = models.TextField(
        _('Description'),
        blank=True,
        help_text=_('Optional description of the category')
    )
    icon = models.ImageField(
        _('Icon'),
        upload_to='vehicle_categories/',
        blank=True,
        help_text=_('Icon representing the category')
    )
    is_active = models.BooleanField(
        _('Active'),
        default=True,
        help_text=_('Whether this category is active and should be displayed')
    )

    class Meta:
        verbose_name = _('Vehicle Category')
        verbose_name_plural = _('Vehicle Categories')
        ordering = ['name']
        db_table = 'vehicle_category'

    def __str__(self):
        return self.name

    def get_available_vehicles(self):
        """Returns all available vehicles in this category."""
        return self.vehicles.filter(is_available=True)

    def get_vehicle_count(self):
        """Returns the total number of vehicles in this category."""
        return self.vehicles.count() 