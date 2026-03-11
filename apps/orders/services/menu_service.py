from django.db import transaction
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError

from ..models import MenuItem, MenuItemImage


class MenuService:
    """Service class for managing menu items."""

    @classmethod
    @transaction.atomic
    def create_menu_item(cls, business_location, food_category, data, images=None):
        """
        Create a new menu item with optional images.
        
        Args:
            business_location: BusinessLocation instance
            food_category: FoodCategory instance
            data: Dict containing menu item data
            images: Optional list of image files
        """
        # Create menu item
        menu_item = MenuItem.objects.create(
            business_location=business_location,
            food_category=food_category,
            **data
        )

        # Add images if provided
        if images:
            for index, image in enumerate(images):
                MenuItemImage.objects.create(
                    menu_item=menu_item,
                    image=image,
                    order=index
                )

        return menu_item

    @classmethod
    @transaction.atomic
    def update_menu_item(cls, menu_item, data, images=None):
        """
        Update an existing menu item.
        
        Args:
            menu_item: MenuItem instance
            data: Dict containing updated menu item data
            images: Optional list of new image files
        """
        # Update menu item fields
        for key, value in data.items():
            setattr(menu_item, key, value)
        menu_item.save()

        # Handle images if provided
        if images:
            # Remove existing images if replace_images is True
            if data.get('replace_images'):
                menu_item.images.all().delete()

            # Add new images
            current_max_order = menu_item.images.count()
            for index, image in enumerate(images):
                MenuItemImage.objects.create(
                    menu_item=menu_item,
                    image=image,
                    order=current_max_order + index
                )

        return menu_item

    @classmethod
    def toggle_availability(cls, menu_item, is_available=None):
        """
        Toggle or set the availability of a menu item.
        
        Args:
            menu_item: MenuItem instance
            is_available: Optional boolean to set specific availability
        """
        if is_available is None:
            menu_item.is_available = not menu_item.is_available
        else:
            menu_item.is_available = is_available
        menu_item.save()
        return menu_item

    @classmethod
    def bulk_update_prices(cls, menu_items, price_change, change_type='fixed'):
        """
        Update prices for multiple menu items.
        
        Args:
            menu_items: QuerySet of MenuItem instances
            price_change: Amount to change (positive or negative)
            change_type: 'fixed' for absolute change or 'percentage' for relative
        """
        if change_type not in ['fixed', 'percentage']:
            raise ValidationError(_("Invalid price change type"))

        with transaction.atomic():
            for item in menu_items:
                if change_type == 'fixed':
                    item.price += price_change
                else:
                    item.price *= (1 + price_change / 100)
                
                if item.price < 0:
                    raise ValidationError(
                        _("Price cannot be negative for item: %(item)s") % 
                        {'item': item.name}
                    )
                
                item.save()

        return menu_items 