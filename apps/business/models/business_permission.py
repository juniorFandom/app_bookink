from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.utils import timezone
from apps.core.models import TimeStampedModel
from .business_location import BusinessLocation
from django.contrib.auth import get_user_model

User = get_user_model()

class BusinessPermission(TimeStampedModel):
    """
    Permissions accordées aux utilisateurs pour gérer un établissement
    """
    # Permissions générales (tous types d'établissements)
    GENERAL_PERMISSIONS = [
        ('view_dashboard', 'Accès au dashboard'),
        ('view_reports', 'Consultation des rapports'),
        ('view_settings', 'Consultation des paramètres'),
    ]
    
    # Permissions spécifiques aux hôtels
    HOTEL_PERMISSIONS = [
        ('manage_rooms', 'Gestion des chambres'),
        ('manage_bookings', 'Gestion des réservations'),
        ('manage_customers', 'Gestion des clients'),
        ('manage_housekeeping', 'Gestion du ménage'),
        ('manage_amenities', 'Gestion des équipements'),
    ]
    
    # Permissions spécifiques aux restaurants
    RESTAURANT_PERMISSIONS = [
        ('manage_menu', 'Gestion du menu'),
        ('manage_orders', 'Gestion des commandes'),
        ('manage_tables', 'Gestion des tables'),
        ('manage_reservations', 'Gestion des réservations'),
        ('manage_inventory', 'Gestion des stocks'),
    ]
    
    # Permissions spécifiques aux locations de véhicules
    VEHICLE_PERMISSIONS = [
        ('manage_vehicles', 'Gestion des véhicules'),
        ('manage_rentals', 'Gestion des locations'),
        ('manage_drivers', 'Gestion des chauffeurs'),
        ('manage_maintenance', 'Gestion de la maintenance'),
        ('manage_insurance', 'Gestion des assurances'),
    ]
    
    # Permissions spécifiques aux tours
    TOUR_PERMISSIONS = [
        ('manage_activities', 'Gestion des activités'),
        ('manage_bookings', 'Gestion des réservations'),
        ('manage_guides', 'Gestion des guides'),
        ('manage_itineraries', 'Gestion des itinéraires'),
        ('manage_customers', 'Gestion des clients'),
    ]
    
    # Toutes les permissions disponibles
    PERMISSION_TYPES = GENERAL_PERMISSIONS + HOTEL_PERMISSIONS + RESTAURANT_PERMISSIONS + VEHICLE_PERMISSIONS + TOUR_PERMISSIONS
    
    business_location = models.ForeignKey(
        BusinessLocation,
        on_delete=models.CASCADE,
        related_name='permissions',
        verbose_name=_('Établissement')
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='business_permissions',
        verbose_name=_('Utilisateur')
    )
    permission_type = models.CharField(
        max_length=50,
        choices=PERMISSION_TYPES,
        verbose_name=_('Type de permission')
    )
    granted_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name='granted_permissions',
        verbose_name=_('Accordé par')
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Expire le')
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Actif')
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_('Notes')
    )
    
    class Meta:
        verbose_name = _('Permission d\'établissement')
        verbose_name_plural = _('Permissions d\'établissements')
        unique_together = ['business_location', 'user', 'permission_type']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_permission_type_display()} - {self.business_location.name}"
    
    @property
    def is_expired(self):
        """Vérifie si la permission est expirée"""
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at
    
    def get_available_permissions_for_location(self):
        """Retourne les permissions disponibles selon le type d'établissement"""
        location_type = self.business_location.business_location_type
        
        if location_type == 'hotel':
            return self.GENERAL_PERMISSIONS + self.HOTEL_PERMISSIONS
        elif location_type == 'restaurant':
            return self.GENERAL_PERMISSIONS + self.RESTAURANT_PERMISSIONS
        elif location_type == 'vehicle_rental':
            return self.GENERAL_PERMISSIONS + self.VEHICLE_PERMISSIONS
        elif location_type == 'tour':
            return self.GENERAL_PERMISSIONS + self.TOUR_PERMISSIONS
        else:
            return self.GENERAL_PERMISSIONS


class PermissionRequest(TimeStampedModel):
    """
    Model for permission requests from users
    """
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
    ]
    
    business_location = models.ForeignKey(
        BusinessLocation,
        on_delete=models.CASCADE,
        related_name='permission_requests',
        verbose_name=_('Business Location')
    )
    
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='permission_requests',
        verbose_name=_('Requester')
    )
    
    permission_type = models.CharField(
        _('Permission Type'),
        max_length=50,
        choices=BusinessPermission.PERMISSION_TYPES
    )
    
    requested_expires_at = models.DateTimeField(
        _('Requested Expiration'),
        null=True,
        blank=True
    )
    
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='reviewed_permission_requests',
        verbose_name=_('Reviewed By'),
        null=True,
        blank=True
    )
    
    reviewed_at = models.DateTimeField(
        _('Reviewed At'),
        null=True,
        blank=True
    )
    
    review_notes = models.TextField(
        _('Review Notes'),
        blank=True
    )

    class Meta:
        verbose_name = _('Permission Request')
        verbose_name_plural = _('Permission Requests')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['business_location', 'requester']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.requester.username} - {self.get_permission_type_display()} on {self.business_location.name}"

    def approve(self, reviewer, notes=''):
        """Approve the permission request"""
        self.status = 'approved'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        self.save()
        
        # Create the actual permission
        BusinessPermission.objects.create(
            business_location=self.business_location,
            user=self.requester,
            permission_type=self.permission_type,
            granted_by=reviewer,
            expires_at=self.requested_expires_at,
            notes=notes
        )

    def reject(self, reviewer, notes=''):
        """Reject the permission request"""
        self.status = 'rejected'
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.review_notes = notes
        self.save()


class UserActionLog(models.Model):
    """
    Trace toutes les actions des utilisateurs sur les dashboards
    """
    ACTION_TYPES = [
        ('view', 'Consultation'),
        ('create', 'Création'),
        ('edit', 'Modification'),
        ('delete', 'Suppression'),
        ('export', 'Export'),
        ('import', 'Import'),
        ('login', 'Connexion'),
        ('logout', 'Déconnexion'),
        ('permission_grant', 'Accord de permission'),
        ('permission_revoke', 'Révocation de permission'),
        ('dashboard_access', 'Accès au dashboard'),
    ]
    
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE,
        related_name='action_logs',
        verbose_name=_('Utilisateur')
    )
    business_location = models.ForeignKey(
        BusinessLocation,
        on_delete=models.CASCADE,
        related_name='user_actions',
        verbose_name=_('Établissement')
    )
    action_type = models.CharField(
        max_length=20,
        choices=ACTION_TYPES,
        verbose_name=_('Type d\'action')
    )
    action_description = models.TextField(
        verbose_name=_('Description de l\'action')
    )
    ip_address = models.GenericIPAddressField(
        null=True, 
        blank=True,
        verbose_name=_('Adresse IP')
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name=_('User Agent')
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Date de création')
    )
    
    class Meta:
        verbose_name = _('Journal d\'action utilisateur')
        verbose_name_plural = _('Journaux d\'actions utilisateurs')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'business_location', 'action_type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_action_type_display()} - {self.business_location.name} - {self.created_at}" 