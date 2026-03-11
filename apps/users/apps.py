from django.apps import AppConfig


class UsersConfig(AppConfig):
    """Configuration class for the users app."""
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.users'
    verbose_name = 'Users'

    def ready(self):
        """Import signals when the app is ready."""
        try:
            import apps.users.signals  # noqa
        except ImportError:
            pass
