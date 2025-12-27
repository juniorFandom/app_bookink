from django import template
from django.utils.translation import gettext_lazy as _

register = template.Library()


@register.filter
def filter_by_category(menu_items, category):
    """
    Filter menu items by category.
    
    Usage: {{ menu_items|filter_by_category:category }}
    """
    return menu_items.filter(food_category=category) 