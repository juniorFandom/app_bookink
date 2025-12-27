from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils.translation import gettext_lazy as _
from .base import TimeStampedModel

class Review(TimeStampedModel):
    """Base review model for different types of content."""
    CONTENT_TYPE_CHOICES = [
        ('business', _('Business')),
        ('guide', _('Guide')),
        ('tour_package', _('Tour Package')),
        ('room', _('Room')),
        ('vehicle', _('Vehicle')),
        ('restaurant', _('Restaurant')),
        ('tour', _('Tour')),
    ]

    reviewer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reviews',
        verbose_name=_('Reviewer')
    )
    content_type = models.CharField(
        max_length=50,
        choices=CONTENT_TYPE_CHOICES,
        verbose_name=_('Content Type')
    )
    object_id = models.IntegerField(verbose_name=_('Object ID'))
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        verbose_name=_('Rating')
    )
    content = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Content')
    )
    is_approved = models.BooleanField(
        default=True,
        verbose_name=_('Is Approved')
    )
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_reviews',
        verbose_name=_('Approved By')
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Approved At')
    )
    response_text = models.TextField(
        blank=True,
        null=True,
        verbose_name=_('Response')
    )
    response_date = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Response Date')
    )
    is_verified_purchase = models.BooleanField(
        default=False,
        verbose_name=_('Verified Purchase')
    )
    helpful_count = models.IntegerField(
        default=0,
        verbose_name=_('Helpful Count')
    )
    is_featured = models.BooleanField(
        default=False,
        verbose_name=_('Featured')
    )
    is_public = models.BooleanField(
        default=True,
        verbose_name=_('Public')
    )

    class Meta:
        verbose_name = _('Review')
        verbose_name_plural = _('Reviews')
        unique_together = ('reviewer', 'content_type', 'object_id')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_content_type_display()} Review by {self.reviewer.get_full_name() or self.reviewer.username}"

class ReviewImage(TimeStampedModel):
    """Model representing images attached to any review."""
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_('Review')
    )
    image = models.ImageField(
        _('Image'),
        upload_to='reviews/images/',
        help_text=_('Image uploaded with the review')
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
        help_text=_('Order in which the image appears')
    )

    class Meta:
        verbose_name = _('Review Image')
        verbose_name_plural = _('Review Images')
        ordering = ['review', 'order']

    def __str__(self):
        return f"Image {self.order} for {self.review}"


class ReviewVote(TimeStampedModel):
    """Model representing helpful votes on reviews."""
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name='votes',
        verbose_name=_('Review')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='review_votes',
        verbose_name=_('User')
    )
    is_helpful = models.BooleanField(
        _('Is Helpful'),
        help_text=_('Whether the user found this review helpful')
    )

    class Meta:
        verbose_name = _('Review Vote')
        verbose_name_plural = _('Review Votes')
        unique_together = [['review', 'user']]
        ordering = ['-created_at']

    def __str__(self):
        return f"Vote by {self.user.get_full_name() or self.user.username} on {self.review}"

    def save(self, *args, **kwargs):
        """Override save to update review helpful votes count."""
        is_new = self.pk is None
        old_is_helpful = None
        
        if not is_new:
            old_is_helpful = ReviewVote.objects.get(pk=self.pk).is_helpful
            
        super().save(*args, **kwargs)
        
        # Update helpful_votes count
        if is_new and self.is_helpful:
            self.review.helpful_count += 1
            self.review.save()
        elif not is_new and old_is_helpful != self.is_helpful:
            if self.is_helpful:
                self.review.helpful_count += 1
            else:
                self.review.helpful_count -= 1
            self.review.save()