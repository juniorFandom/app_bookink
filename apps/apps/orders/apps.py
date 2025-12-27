from django.apps import AppConfig


class OrdersConfig(AppConfig):
    """
    Configuration for the Orders application.
    
    This app manages restaurant orders, menu items, and food categories
    for the tourism platform's restaurant management system.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.orders'
    verbose_name = 'Restaurant Orders'

    def ready(self):
        """
        Perform initialization tasks when the app is ready.
        Import signal handlers if any.
        """
        try:
            import apps.orders.signals  # noqa
        except ImportError:
            pass
