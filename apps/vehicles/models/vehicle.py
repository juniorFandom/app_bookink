from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from apps.business.models import BusinessLocation
from .category import VehicleCategory

class Vehicle(models.Model):
    """
    Model representing a vehicle available for rental.
    """
    TRANSMISSION_CHOICES = [
        ('MANUAL', _('Manual')),
        ('AUTOMATIC', _('Automatic')),
    ]

    FUEL_TYPE_CHOICES = [
        ('PETROL', _('Petrol')),
        ('DIESEL', _('Diesel')),
        ('ELECTRIC', _('Electric')),
        ('HYBRID', _('Hybrid')),
    ]

    business_location = models.ForeignKey(
        BusinessLocation,
        on_delete=models.CASCADE,
        related_name='vehicles',
        verbose_name=_('Business Location')
    )
    vehicle_category = models.ForeignKey(
        VehicleCategory,
        on_delete=models.PROTECT,
        related_name='vehicles',
        verbose_name=_('Vehicle Category')
    )
    make = models.CharField(
        _('Make'),
        max_length=100,
        help_text=_('Vehicle manufacturer')
    )
    model = models.CharField(
        _('Model'),
        max_length=100,
        help_text=_('Vehicle model')
    )
    year = models.IntegerField(
        _('Year'),
        help_text=_('Manufacturing year')
    )
    license_plate = models.CharField(
        _('License Plate'),
        max_length=50,
        unique=True,
        help_text=_('Vehicle license plate number')
    )
    color = models.CharField(
        _('Color'),
        max_length=50,
        help_text=_('Vehicle color')
    )
    passenger_capacity = models.IntegerField(
        _('Passenger Capacity'),
        help_text=_('Maximum number of passengers')
    )
    transmission = models.CharField(
        _('Transmission'),
        max_length=20,
        choices=TRANSMISSION_CHOICES,
        help_text=_('Transmission type')
    )
    fuel_type = models.CharField(
        _('Fuel Type'),
        max_length=20,
        choices=FUEL_TYPE_CHOICES,
        help_text=_('Type of fuel used')
    )
    daily_rate = models.DecimalField(
        _('Daily Rate'),
        max_digits=10,
        decimal_places=2,
        help_text=_('Daily rental rate in XAF')
    )
    driver_daily_rate = models.DecimalField(
        _('Tarif chauffeur par jour (FCFA)'),
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text=_('Tarif journalier du chauffeur pour ce véhicule')
    )
    description = models.TextField(
        _('Description'),
        blank=True,
        help_text=_('Detailed description of the vehicle')
    )
    features = models.JSONField(
        _('Features'),
        default=list,
        blank=True,
        help_text=_('List of vehicle features')
    )
    main_image = models.ImageField(
        _('Main Image'),
        upload_to='vehicles/',
        blank=True,
        help_text=_('Primary image of the vehicle')
    )
    mileage = models.IntegerField(
        _('Mileage'),
        default=0,
        help_text=_('Current mileage of the vehicle')
    )
    is_available = models.BooleanField(
        _('Available'),
        default=True,
        help_text=_('Whether this vehicle is currently available for rent')
    )
    maintenance_mode = models.BooleanField(
        _('Maintenance Mode'),
        default=False,
        help_text=_('Whether this vehicle is under maintenance')
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
        verbose_name = _('Vehicle')
        verbose_name_plural = _('Vehicles')
        ordering = ['-created_at']
        db_table = 'vehicle'

    def __str__(self):
        return f"{self.year} {self.make} {self.model} ({self.license_plate})"

    def get_display_name(self):
        """Returns a formatted display name for the vehicle."""
        return f"{self.make} {self.model} ({self.year})"

    def is_rentable(self):
        """Checks if the vehicle can be rented."""
        return self.is_available and not self.maintenance_mode

    def update_mileage(self, new_mileage):
        """Updates the vehicle's mileage."""
        if new_mileage > self.mileage:
            self.mileage = new_mileage
            self.save(update_fields=['mileage', 'updated_at'])

class VehicleImage(models.Model):
    """
    Model representing additional images for a vehicle.
    """
    vehicle = models.ForeignKey(
        Vehicle,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_('Vehicle')
    )
    image = models.ImageField(
        _('Image'),
        upload_to='vehicles/',
        help_text=_('Additional image of the vehicle')
    )
    caption = models.CharField(
        _('Caption'),
        max_length=255,
        blank=True,
        help_text=_('Optional caption for the image')
    )
    order = models.IntegerField(
        _('Display Order'),
        default=0,
        help_text=_('Order in which the image appears in the gallery')
    )
    created_at = models.DateTimeField(
        _('Created At'),
        auto_now_add=True
    )

    class Meta:
        verbose_name = _('Vehicle Image')
        verbose_name_plural = _('Vehicle Images')
        ordering = ['order']
        db_table = 'vehicle_image'

    def __str__(self):
        return f"Image {self.order} for {self.vehicle}" 