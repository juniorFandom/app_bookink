from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class BusinessConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.business'
    verbose_name = _('Business Management')
    
    def ready(self):
        try:
            import apps.business.signals  # noqa
        except ImportError:
            pass
