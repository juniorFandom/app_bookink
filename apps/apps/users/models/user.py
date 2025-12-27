from django.contrib.contenttypes.fields import GenericRelation
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import TimeStampedModel
from .role import Role, UserRole

class User(TimeStampedModel, AbstractUser):
    """Custom user model extending Django's AbstractUser.
    
    Adds additional fields for the tourism platform requirements.
    """
    roles = models.ManyToManyField(
        Role,
        through=UserRole,
        through_fields=('user', 'role'),
        related_name='users',
        help_text='Les rôles attribués à cet utilisateur'
    )

    email = models.EmailField(_('email address'), unique=True)
    phone_number = models.CharField(_('phone number'), max_length=20, blank=True)
    avatar = models.ImageField(_('avatar'), upload_to='avatars/', blank=True)
    date_of_birth = models.DateField(_('date of birth'), null=True, blank=True)
    gender = models.CharField(
        _('gender'),
        max_length=10,
        choices=[('M', 'Male'), ('F', 'Female'), ('OTHER', 'Other')],
        blank=True
    )
    language_preference = models.CharField(
        _('language preference'),
        max_length=10,
        default='en',
        choices=[('en', 'English'), ('fr', 'French')]
    )
    ville = models.CharField(
        _('ville de résidence'),
        max_length=100,
        default='Bandjoun',
        help_text='Ville de résidence de l\'utilisateur'
    )

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')
        db_table = 'user'

    def __str__(self):
        return self.get_full_name() or self.username