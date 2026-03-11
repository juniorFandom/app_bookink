from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import TimeStampedModel


class Role(TimeStampedModel):
    """Role model for flexible user role management."""
    name = models.CharField(_('name'), max_length=50, unique=True)
    code = models.CharField(_('code'), max_length=20, unique=True)
    description = models.TextField(_('description'), blank=True)
    is_active = models.BooleanField(_('active'), default=True)

    class Meta:
        verbose_name = _('role')
        verbose_name_plural = _('roles')
        db_table = 'role'

    def __str__(self):
        return self.name


class UserRole(TimeStampedModel):
    """Many-to-many relationship between users and roles with additional metadata."""
    user = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        verbose_name=_('user'),
        related_name='user_roles'
    )
    role = models.ForeignKey(
        Role,
        on_delete=models.CASCADE,
        verbose_name=_('role'),
        related_name='user_roles'
    )
    assigned_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('assigned by'),
        related_name='role_assignments'
    )

    class Meta:
        verbose_name = _('user role')
        verbose_name_plural = _('user roles')
        db_table = 'user_role'
        unique_together = ('user', 'role')

    def __str__(self):
        return f'{self.user} - {self.role}'