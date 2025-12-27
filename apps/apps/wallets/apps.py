from django.apps import AppConfig


class WalletsConfig(AppConfig):
    """Configuration for the Wallets application."""
    
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.wallets'
    verbose_name = 'Wallets'

    def ready(self):
        """
        Import signal handlers when the app is ready.
        """
        try:
            import apps.wallets.signals  # noqa
        except ImportError:
            pass
