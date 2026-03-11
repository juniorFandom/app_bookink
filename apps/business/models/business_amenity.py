from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import TimeStampedModel
from .business_location import BusinessLocation


class BusinessAmenityCategory(TimeStampedModel):
    """
    Model representing categories of business amenities (e.g., Room Features, Services, etc.)
    """
    name = models.CharField(_('Name'), max_length=100)
    description = models.TextField(_('Description'), blank=True)
    icon = models.CharField(_('Icon Class'), max_length=50, blank=True)
    is_active = models.BooleanField(_('Active'), default=True)

    class Meta:
        verbose_name = _('Business Amenity Category')
        verbose_name_plural = _('Business Amenity Categories')
        ordering = ['name']

    def __str__(self):
        return self.name


class BusinessAmenity(TimeStampedModel):
    """
    Model representing specific amenities that can be assigned to businesses
    """
    category = models.ForeignKey(
        BusinessAmenityCategory,
        on_delete=models.CASCADE,
        related_name='amenities',
        verbose_name=_('Category'),
        null=True,
        blank=True
    )
    name = models.CharField(_('Name'), max_length=100)
    description = models.TextField(_('Description'), blank=True)
    icon = models.CharField(_('Icon Class'), max_length=50, blank=True)
    is_active = models.BooleanField(_('Active'), default=True)

    class Meta:
        verbose_name = _('Business Amenity')
        verbose_name_plural = _('Business Amenities')
        ordering = ['category', 'name']

    def __str__(self):
        return f"{self.category.name} - {self.name}"


class BusinessAmenityAssignment(TimeStampedModel):
    """
    Model representing the assignment of amenities to specific businesses
    """
    business_location = models.ForeignKey(
        BusinessLocation,
        on_delete=models.CASCADE,
        related_name='amenity_assignments',
        verbose_name=_('Business Location'),
        null=True,
        blank=True
    )
    
    amenity = models.ForeignKey(
        BusinessAmenity,
        on_delete=models.CASCADE,
        related_name='business_assignments',
        verbose_name=_('Amenity'),
        null=True,
        blank=True
    )
    
    details = models.TextField(
        _('Additional Details'),
        blank=True,
        help_text=_('Any specific details about this amenity for this business')
    )
    is_active = models.BooleanField(_('Active'), default=True)

    class Meta:
        verbose_name = _('Business Amenity Assignment')
        verbose_name_plural = _('Business Amenity Assignments')
        ordering = ['business_location', 'amenity']
        unique_together = ['business_location', 'amenity']

    def __str__(self):
        return f"{self.business_location.name} - {self.amenity.name}"