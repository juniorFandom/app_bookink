from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class VehiclesConfig(AppConfig):
    """
    Configuration for the Vehicles application.
    
    This app manages vehicle rentals, including vehicle categories,
    vehicle listings, drivers, and rental contracts.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.vehicles'
    verbose_name = _('Vehicle Rentals')

    def ready(self):
        """
        Perform initialization tasks when the app is ready.
        Import signal handlers if any.
        """
        try:
            import apps.vehicles.signals  # noqa
        except ImportError:
            pass