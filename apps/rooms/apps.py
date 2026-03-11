from django.apps import AppConfig


class RoomsConfig(AppConfig):
    """
    Configuration for the Rooms application.
    
    This app manages accommodation-related features including:
    - Room types and categories
    - Room inventory and availability
    - Room amenities and features
    - Room pricing and reservations
    - Room galleries and images
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.rooms'
    verbose_name = 'Rooms'
