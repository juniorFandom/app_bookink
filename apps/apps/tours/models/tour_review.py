from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from apps.core.models import Review
from .tour import Tour

class TourReview(Review):
    
    # Lien vers le tour et la réservation
    tour = models.ForeignKey(
        Tour,
        on_delete=models.CASCADE,
        related_name='tour_reviews',
        verbose_name=_('Tour')
    )
    
    # Ratings détaillés spécifiques aux tours
    guide_rating = models.IntegerField(
        _('Guide Rating'),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text=_('Rating for the tour guide from 1 to 5 stars')
    )
    value_rating = models.IntegerField(
        _('Value for Money Rating'),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text=_('Rating for value for money from 1 to 5 stars')
    )
    activities_rating = models.IntegerField(
        _('Activities Rating'),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text=_('Rating for the activities from 1 to 5 stars')
    )
    transportation_rating = models.IntegerField(
        _('Transportation Rating'),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text=_('Rating for transportation from 1 to 5 stars')
    )
    accommodation_rating = models.IntegerField(
        _('Accommodation Rating'),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True,
        help_text=_('Rating for accommodation from 1 to 5 stars')
    )
    food_rating = models.IntegerField(
        _('Food Rating'),
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        null=True,
        blank=True,
        help_text=_('Rating for food from 1 to 5 stars')
    )
    
    # Champs spécifiques aux tours
    pros = models.TextField(
        _('Pros'),
        blank=True,
        help_text=_('Positive aspects of the tour')
    )
    cons = models.TextField(
        _('Cons'),
        blank=True,
        help_text=_('Negative aspects of the tour')
    )
    tips = models.TextField(
        _('Tips'),
        blank=True,
        help_text=_('Tips for future travelers')
    )
    would_recommend = models.BooleanField(
        _('Would Recommend'),
        help_text=_('Whether the reviewer would recommend this tour')
    )

    class Meta:
        verbose_name = _('Tour Review')
        verbose_name_plural = _('Tour Reviews')
        ordering = ['-created_at']
        unique_together = [['tour']]

    def __str__(self):
        return f"{self.reviewer}'s review of {self.tour}"

    def get_absolute_url(self):
        """Returns the URL to access a detail record for this review."""
        from django.urls import reverse
        return reverse('tours:review_detail', kwargs={'pk': self.pk})

    def calculate_average_rating(self):
        """Calculate the average rating across all rating categories."""
        ratings = [
            self.rating,
            self.guide_rating,
            self.value_rating,
            self.activities_rating,
            self.transportation_rating
        ]
        
        if self.accommodation_rating:
            ratings.append(self.accommodation_rating)
        if self.food_rating:
            ratings.append(self.food_rating)
            
        return sum(ratings) / len(ratings)

    def save(self, *args, **kwargs):
        """Override save to set content_type, object_id and verified status."""
        # Définir automatiquement le content_type et object_id
        self.content_type = 'tour'
        if self.tour:
            self.object_id = self.tour.id
        
        # Vérifier si c'est un achat vérifié
        if self.booking:
            self.is_verified_purchase = True
        
        super().save(*args, **kwargs)