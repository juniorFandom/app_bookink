from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from apps.business.models import BusinessLocation
from apps.users.models import User

class Driver(models.Model):
    """
    Model representing a driver who can be assigned to vehicle rentals.
    """
    GENDER_CHOICES = [
        ('M', _('Male')),
        ('F', _('Female')),
    ]

    LICENSE_TYPES = [
        ('A', _('Type A')),
        ('B', _('Type B')),
        ('C', _('Type C')),
        ('D', _('Type D')),
        ('E', _('Type E')),
    ]

    business_location = models.ForeignKey(
        BusinessLocation,
        on_delete=models.CASCADE,
        related_name='drivers',
        verbose_name=_('Business Location')
    )
    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        related_name='driver_profile',
        verbose_name=_('User Account'),
        null=True,
        blank=True
    )
    first_name = models.CharField(
        _('First Name'),
        max_length=100
    )
    last_name = models.CharField(
        _('Last Name'),
        max_length=100
    )
    gender = models.CharField(
        _('Gender'),
        max_length=1,
        choices=GENDER_CHOICES
    )
    date_of_birth = models.DateField(
        _('Date of Birth')
    )
    phone_number = models.CharField(
        _('Phone Number'),
        max_length=20
    )
    email = models.EmailField(
        _('Email'),
        blank=True
    )
    address = models.TextField(
        _('Address')
    )
    license_number = models.CharField(
        _('License Number'),
        max_length=50,
        unique=True
    )
    license_type = models.CharField(
        _('License Type'),
        max_length=1,
        choices=LICENSE_TYPES
    )
    license_expiry = models.DateField(
        _('License Expiry Date')
    )
    photo = models.ImageField(
        _('Photo'),
        upload_to='drivers/photos/',
        blank=True
    )
    years_of_experience = models.PositiveIntegerField(
        _('Years of Experience'),
        default=0
    )
    languages_spoken = models.JSONField(
        _('Languages Spoken'),
        default=list,
        help_text=_('List of language codes')
    )
    daily_rate = models.DecimalField(
        _('Daily Rate'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    is_available = models.BooleanField(
        _('Available'),
        default=True
    )
    is_verified = models.BooleanField(
        _('Is Verified'),
        default=False
    )
    verification_document = models.FileField(
        _('Verification Document'),
        upload_to='drivers/verification/',
        blank=True
    )
    notes = models.TextField(
        _('Notes'),
        blank=True
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
        verbose_name = _('Driver')
        verbose_name_plural = _('Drivers')
        ordering = ['last_name', 'first_name']
        db_table = 'driver'

    def __str__(self):
        return f"{self.first_name} {self.last_name}"

    @property
    def full_name(self):
        """Returns the driver's full name."""
        return f"{self.first_name} {self.last_name}"

    def is_license_valid(self):
        """Checks if the driver's license is still valid."""
        from django.utils import timezone
        return self.license_expiry > timezone.now().date()

    def get_active_bookings(self):
        """Returns all active bookings assigned to this driver."""
        return self.vehicle_bookings.filter(status='ACTIVE') 