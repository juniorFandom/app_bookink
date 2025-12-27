from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import TimeStampedModel
from apps.core.models import Address
from .business import Business
from django.conf import settings
from django.db.models.signals import post_save
from django.dispatch import receiver

class BusinessLocation(Address):
    """
    Model representing a physical location of a business (branch, office, etc.)
    """
    BUSINESS_TYPES = [
        ('hotel', _('Hotel')),
        ('restaurant', _('Restaurant')),
        ('tour_operator', _('Tour Operator')),
        ('transport', _('Transport Company')),
        ('other', _('Other')),
    ]
    
    business = models.ForeignKey(
        Business,
        on_delete=models.CASCADE,
        related_name='locations',
        verbose_name=_('Business'),
        null=True,
        blank=True
    )
    
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='owned_business_locations',
        verbose_name=_('Business Owner'),
        null=True,
        blank=True
    )
    
    business_location_type = models.CharField(
        _('Business Location Type'),
        max_length=50,
        choices=BUSINESS_TYPES,
        null=True,
        blank=True
    )
    
    name = models.CharField(
        _('Location Name'),
        max_length=255,
        help_text=_('Name of this business location/branch')
    )
    
    phone = models.CharField(
        _('Phone Number'),
        max_length=20,
        blank=True
    )
    
    email = models.EmailField(
        _('Email'),
        blank=True
    )
    
    registration_number = models.CharField(
        _('Registration Number'),
        max_length=100,
        unique=True
    )
    
    # Business Details
    description = models.TextField(
        _('Business Description')
    )
    
    founded_date = models.DateField(
        _('Founded Date'),
        null=True,
        blank=True
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
    
    featured = models.BooleanField(
        _('Featured'),
        default=False
    )
    
    is_main_location = models.BooleanField(
        _('Main Location'),
        default=False,
        help_text=_('Whether this is the main location of the business')
    )

    class Meta:
        verbose_name = _('Business Location')
        verbose_name_plural = _('Business Locations')
        ordering = ['-is_main_location', 'name']
        indexes = [
            models.Index(fields=['business']),
            models.Index(fields=['is_main_location']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.business.name} - {self.name}"

    def save(self, *args, **kwargs):
        if self.is_main_location:
            # Ensure only one main location per business
            BusinessLocation.objects.filter(
                business=self.business,
                is_main_location=True
            ).exclude(pk=self.pk).update(is_main_location=False)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('business:location_detail', kwargs={'pk': self.pk})
    
class BusinessLocationImage(TimeStampedModel):
    """
    Model for managing business location images
    """
    business_location = models.ForeignKey(
        BusinessLocation,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_('Business Location'),
        null=True,
        blank=True
    )
    image = models.ImageField(_('Image'), upload_to='business_location_images/')
    caption = models.CharField(_('Caption'), max_length=255, blank=True)
    is_primary = models.BooleanField(_('Primary Image'), default=False)

    class Meta:
        verbose_name = _('Business Location Image')
        verbose_name_plural = _('Business Location Images')
        ordering = ['-is_primary', '-created_at']

    def __str__(self):
        return f"Image for {self.business_location.name}"

    def save(self, *args, **kwargs):
        if self.is_primary:
            BusinessLocationImage.objects.filter(
                business_location=self.business_location,
                is_primary=True
            ).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)

@receiver(post_save, sender=BusinessLocation)
def create_wallet_for_business_location(sender, instance, created, **kwargs):
    if created and not hasattr(instance, 'wallet'):
        from apps.wallets.models.wallet import BusinessLocationWallet
        BusinessLocationWallet.objects.create(business_location=instance)

class BusinessLocationDocument(TimeStampedModel):
    """
    Model for managing business location documents/files
    """
    business_location = models.ForeignKey(
        BusinessLocation,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name=_('Business Location'),
        null=True,
        blank=True
    )
    file = models.FileField(_('Document'), upload_to='business_location_documents/')
    title = models.CharField(_('Document Title'), max_length=255)
    description = models.TextField(_('Description'), blank=True)
    document_type = models.CharField(
        _('Document Type'),
        max_length=50,
        choices=[
            ('license', _('License')),
            ('permit', _('Permit')),
            ('contract', _('Contract')),
            ('certificate', _('Certificate')),
            ('insurance', _('Insurance')),
            ('other', _('Other')),
        ],
        default='other'
    )

    class Meta:
        verbose_name = _('Business Location Document')
        verbose_name_plural = _('Business Location Documents')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.title} - {self.business_location.name}"

    def get_file_extension(self):
        """Get the file extension"""
        import os
        return os.path.splitext(self.file.name)[1].lower()

    def get_file_size(self):
        """Get the file size in bytes"""
        try:
            return self.file.size
        except:
            return 0

    def get_file_size_display(self):
        """Get the file size in human readable format"""
        size = self.get_file_size()
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"