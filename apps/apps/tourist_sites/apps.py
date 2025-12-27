from django.apps import AppConfig


class TouristSitesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.tourist_sites'
    verbose_name = 'Sites Touristiques'

    def ready(self):
        import apps.tourist_sites.signals 