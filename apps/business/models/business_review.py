from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.core.models import Review
from .business_location import BusinessLocation

class BusinessReview(Review):
    """
    Model for storing customer reviews and ratings for businesses
    Inherits from Review for common review functionality
    """
    business_location = models.ForeignKey(
        BusinessLocation,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=_('Business Location'),
        null=True,
        blank=True
    )
    
    # Additional rating categories specific to businesses
    service_rating = models.PositiveSmallIntegerField(
        _('Service Rating'),
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    
    value_rating = models.PositiveSmallIntegerField(
        _('Value for Money'),
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    
    cleanliness_rating = models.PositiveSmallIntegerField(
        _('Cleanliness Rating'),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    
    location_rating = models.PositiveSmallIntegerField(
        _('Location Rating'),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True
    )
    
    # Business-specific fields
    visit_date = models.DateField(
        _('Visit Date'),
        help_text=_('Date when the reviewer visited the business')
    )
    
    visit_type = models.CharField(
        _('Visit Type'),
        max_length=20,
        choices=[
            ('BUSINESS', _('Business')),
            ('COUPLES', _('Couples')),
            ('FAMILY', _('Family')),
            ('FRIENDS', _('Friends')),
            ('SOLO', _('Solo')),
        ]
    )
    
    # Override Meta to add business-specific constraints and indexes
    class Meta:
        verbose_name = _('Business Review')
        verbose_name_plural = _('Business Reviews')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['business_location']),
        ]
        constraints = [
            # models.UniqueConstraint(
            #     fields=['business_location', 'reviewer', 'visit_date'],
            #     name='unique_business_location_user_visit_review'
            # )
        ]

    def save(self, *args, **kwargs):
        # Automatically set content_type and object_id for business_location reviews
        self.content_type = 'business_location'
        self.object_id = self.business_location.id
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.business_location.name} - {self.rating}★ by {self.reviewer.get_full_name() or self.reviewer.username}"

    def calculate_average_rating(self):
        """
        Calculate the average rating across all rating categories
        """
        ratings = [
            self.rating,  # overall rating from parent Review
            self.service_rating,
            self.value_rating,
            self.cleanliness_rating,
            self.location_rating,
        ]
        
        return sum(ratings) / len(ratings)

    @property
    def overall_rating(self):
        """
        Property to maintain backward compatibility
        Maps to the rating field from parent Review
        """
        return self.rating

    @overall_rating.setter
    def overall_rating(self, value):
        """
        Setter to maintain backward compatibility
        """
        self.rating = value