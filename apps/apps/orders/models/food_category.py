from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import TimeStampedModel


class FoodCategory(TimeStampedModel):
    """
    Model representing a food category in the restaurant menu.
    """
    name = models.CharField(
        _('Name'),
        max_length=100,
        unique=True,
        help_text=_('Category name (e.g. Appetizers, Main Course, Desserts)')
    )
    description = models.TextField(
        _('Description'),
        blank=True,
        help_text=_('Optional description of the category')
    )
    image = models.ImageField(
        _('Image'),
        upload_to='food_categories/',
        blank=True,
        help_text=_('Optional category image')
    )
    order = models.IntegerField(
        _('Display Order'),
        default=0,
        help_text=_('Order in which the category appears in listings')
    )
    is_active = models.BooleanField(
        _('Active'),
        default=True,
        help_text=_('Whether this category is active and should be displayed')
    )

    class Meta:
        verbose_name = _('Food Category')
        verbose_name_plural = _('Food Categories')
        ordering = ['order', 'name']

    def __str__(self):
        return self.name

    def get_active_menu_items(self):
        """Returns all active menu items in this category."""
        return self.menu_items.filter(is_available=True)