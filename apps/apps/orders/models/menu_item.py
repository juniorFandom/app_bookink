from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.text import slugify
from apps.business.models import BusinessLocation


class MenuItem(models.Model):
    """
    Model representing a menu item in a restaurant.
    """
    business_location = models.ForeignKey(
        BusinessLocation,
        on_delete=models.CASCADE,
        related_name='menu_items',
        verbose_name=_('Business Location')
    )
    food_category = models.ForeignKey(
        'orders.FoodCategory',
        on_delete=models.PROTECT,
        related_name='menu_items',
        verbose_name=_('Food Category')
    )
    name = models.CharField(
        _('Name'),
        max_length=200,
        help_text=_('Name of the menu item')
    )
    slug = models.SlugField(
        _('Slug'),
        max_length=255,
        help_text=_('URL-friendly version of the menu item name')
    )
    description = models.TextField(
        _('Description'),
        blank=True,
        help_text=_('Detailed description of the menu item')
    )
    price = models.DecimalField(
        _('Price'),
        max_digits=10,
        decimal_places=2,
        help_text=_('Price in XAF')
    )
    preparation_time_minutes = models.IntegerField(
        _('Preparation Time'),
        null=True,
        blank=True,
        help_text=_('Estimated preparation time in minutes')
    )
    calories = models.IntegerField(
        _('Calories'),
        null=True,
        blank=True,
        help_text=_('Caloric content')
    )
    ingredients = models.JSONField(
        _('Ingredients'),
        default=list,
        blank=True,
        help_text=_('List of ingredients')
    )
    allergens = models.JSONField(
        _('Allergens'),
        default=list,
        blank=True,
        help_text=_('List of allergens')
    )
    dietary_info = models.JSONField(
        _('Dietary Information'),
        default=list,
        blank=True,
        help_text=_('Dietary information (vegetarian, vegan, etc.)')
    )
    main_image = models.ImageField(
        _('Main Image'),
        upload_to='menu_items/',
        blank=True,
        help_text=_('Primary image of the menu item')
    )
    is_available = models.BooleanField(
        _('Available'),
        default=True,
        help_text=_('Whether this item is currently available')
    )
    is_featured = models.BooleanField(
        _('Featured'),
        default=False,
        help_text=_('Whether this item should be featured')
    )
    order = models.IntegerField(
        _('Display Order'),
        default=0,
        help_text=_('Order in which the item appears in listings')
    )
    stock_quantity = models.PositiveIntegerField(
        _('Stock disponible'),
        default=0,
        help_text=_('Nombre de plats disponibles à la vente')
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
        verbose_name = _('Menu Item')
        verbose_name_plural = _('Menu Items')
        ordering = ['food_category', 'order', 'name']
        db_table = 'menu_item'
        unique_together = [['business_location', 'slug']]

    def __str__(self):
        return f"{self.name} - {self.business_location}"

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        if self.stock_quantity == 0:
            self.is_available = False
        super().save(*args, **kwargs)


class MenuItemImage(models.Model):
    """
    Model representing additional images for a menu item.
    """
    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_('Menu Item')
    )
    image = models.ImageField(
        _('Image'),
        upload_to='menu_items/',
        help_text=_('Additional image of the menu item')
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
        help_text=_('Order in which the image appears in the gallery')
    )
    created_at = models.DateTimeField(
        _('Created At'),
        auto_now_add=True
    )

    class Meta:
        verbose_name = _('Menu Item Image')
        verbose_name_plural = _('Menu Item Images')
        ordering = ['order']
        db_table = 'menu_item_image'

    def __str__(self):
        return f"Image {self.order} for {self.menu_item.name}" 