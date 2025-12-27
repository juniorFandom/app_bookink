from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from apps.core.models import TimeStampedModel
from decimal import Decimal


class Business(TimeStampedModel):
    """
    Model representing a tourism-related business
    """
    name = models.CharField(_('Business Name'), max_length=255)
    
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_businesses',
        verbose_name=_('Business Owner'),
        null=True,
        blank=True
    )
    
    # Contact Information
    email = models.EmailField(_('Business Email'))
    phone = models.CharField(_('Business Phone'), max_length=20)
    website = models.URLField(_('Website'), blank=True)
    
    # Business Details
    description = models.TextField(_('Business Description'))
    founded_date = models.DateField(_('Founded Date'), null=True, blank=True)
    
    # Commission Configuration
    commission_rate = models.DecimalField(
        _('Commission Rate (%)'),
        max_digits=5,
        decimal_places=2,
        default=Decimal('5.00'),
        help_text=_('Percentage of commission taken by the platform (e.g., 5.00 for 5%)')
    )
    
    # Status and Verification
    is_active = models.BooleanField(
        _('Active'),
        default=True
    )
    
    is_verified = models.BooleanField(
        _('Verified'),
        default=False
    )

    class Meta:
        verbose_name = _('Business')
        verbose_name_plural = _('Businesses')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['is_verified']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.name}"

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('business:business-detail', kwargs={'pk': self.pk})
    
    def calculate_commission(self, amount):
        """
        Calculate commission amount for a given transaction amount
        """
        return (amount * self.commission_rate) / 100