from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import Address, TimeStampedModel
from .tour import Tour

class TourDestination(Address):
    """
    Model representing a tourist destination.
    """
    tour = models.ForeignKey(
        Tour,
        on_delete=models.CASCADE,
        related_name='destinations',
        verbose_name=_('Tour')
    )
    name = models.CharField(
        _('Name'),
        max_length=255,
        help_text=_('Name of the destination')
    )
    slug = models.SlugField(
        _('Slug'),
        max_length=255,
        unique=True,
        help_text=_('URL-friendly version of the name')
    )
    description = models.TextField(
        _('Description'),
        help_text=_('Detailed description of the destination')
    )
    highlights = models.JSONField(
        _('Highlights'),
        default=list,
        blank=True,
        help_text=_('Key highlights and features of the destination')
    )
    features = models.JSONField(
        _('Features'),
        default=list,
        blank=True,
        help_text=_('List of destination features and attractions')
    )
    best_time_to_visit = models.CharField(
        _('Best Time to Visit'),
        max_length=255,
        blank=True,
        help_text=_('Recommended time period to visit')
    )
    day_number = models.IntegerField(
        _('Day Number'),
        help_text=_('Day of the tour when this destination is visited')
    )
    duration = models.DurationField(
        _('Duration'),
        help_text=_('Time spent at this destination')
    )
    climate = models.TextField(
        _('Climate'),
        blank=True,
        help_text=_('Description of the local climate')
    )
    how_to_get_there = models.TextField(
        _('How to Get There'),
        blank=True,
        help_text=_('Transportation and access information')
    )
    is_active = models.BooleanField(
        _('Active'),
        default=True,
        help_text=_('Whether this destination is active')
    )
    is_featured = models.BooleanField(
        _('Featured'),
        default=False,
        help_text=_('Whether this destination should be featured')
    )

    class Meta:
        verbose_name = _('Destination')
        verbose_name_plural = _('Destinations')
        ordering = ['name']
        db_table = 'destination'

    def __str__(self):
        return f"{self.name} ({self.city}, {self.region})"

    def get_absolute_url(self):
        """Returns the URL to access a detail record for this destination."""
        from django.urls import reverse
        return reverse('tours:destination_detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        """Override save method to automatically generate slug if not provided."""
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            
            # Ensure slug uniqueness
            while TourDestination.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            
            self.slug = slug
        
        super().save(*args, **kwargs)

    def get_nearby_destinations(self, distance_km=50):
        """Returns destinations within the specified distance."""
        return TourDestination.objects.filter(
            location__distance_lte=(self.location, distance_km * 1000)
        ).exclude(pk=self.pk)


class TourDestinationImage(TimeStampedModel):
    """
    Model representing additional images for a destination.
    """
    destination = models.ForeignKey(
        TourDestination,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_('Destination')
    )
    image = models.ImageField(
        _('Image'),
        upload_to='destinations/',
        help_text=_('Additional image of the destination')
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

    class Meta:
        verbose_name = _('Destination Image')
        verbose_name_plural = _('Destination Images')
        ordering = ['order']
        db_table = 'destination_image'

    def __str__(self):
        return f"Image {self.order} for {self.destination}" 