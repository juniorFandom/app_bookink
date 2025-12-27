from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class ToursConfig(AppConfig):
    """
    Configuration for the Tours application.
    
    This app manages tourist circuits, including tour packages,
    destinations, activities, and bookings.
    """
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.tours'
    verbose_name = _('Tourist Circuits')

    def ready(self):
        """
        Perform initialization tasks when the app is ready.
        Import signal handlers if any.
        """
        try:
            import apps.tours.signals  # noqa
        except ImportError:
            pass
