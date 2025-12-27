from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimeStampedModel
from apps.business.models import BusinessLocation


class GuideProfile(TimeStampedModel):
    """Profile model for tour guides."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='guide_profile',
        verbose_name=_('user')
    )
    
    business_location = models.ForeignKey(
        BusinessLocation,
        on_delete=models.CASCADE,
        related_name='guides',
        verbose_name=_('business location')
    )
    
    license_number = models.CharField(
        _('license number'),
        max_length=100,
        blank=True
    )
    
    years_of_experience = models.PositiveIntegerField(
        _('years of experience'),
        default=0
    )
    
    languages_spoken = models.JSONField(
        _('languages spoken'),
        default=list,
        help_text=_('List of language codes')
    )
    
    specializations = models.JSONField(
        _('specializations'),
        default=list,
        help_text=_('List of specialization areas')
    )
    
    hourly_rate = models.DecimalField(
        _('hourly rate'),
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    is_verified = models.BooleanField(
        _('verified'),
        default=False
    )
    
    verification_document = models.FileField(
        _('verification document'),
        upload_to='guides/verification/',
        blank=True
    )
    
    bio = models.TextField(
        _('biography'),
        blank=True
    )

    class Meta:
        verbose_name = _('guide profile')
        verbose_name_plural = _('guide profiles')
        db_table = 'guide_profile'

    def __str__(self):
        return f'Guide Profile: {self.user.get_full_name() or self.user.username}'

    @property
    def full_name(self):
        """Get guide's full name."""
        return self.user.get_full_name() or self.user.username

    @property
    def email(self):
        """Get guide's email."""
        return self.user.email

    @property
    def phone_number(self):
        """Get guide's phone number."""
        return self.user.phone_number