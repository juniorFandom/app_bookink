from django.apps import AppConfig


class GuidesConfig(AppConfig):
    """Configuration class for the guides app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.guides'
    verbose_name = 'Guides'

    def ready(self):
        """Import signals when the app is ready."""
        import apps.guides.signals  # noqa
