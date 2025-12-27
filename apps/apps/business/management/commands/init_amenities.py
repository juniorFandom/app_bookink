from django.core.management.base import BaseCommand
from apps.business.models.business_amenity import BusinessAmenityCategory, BusinessAmenity
from django.utils.translation import gettext_lazy as _

CATEGORIES = [
    {
        'name': _('Services'),
        'icon': 'fa-concierge-bell',
        'amenities': [
            {'name': _('Wi-Fi'), 'icon': 'fa-wifi'},
            {'name': _('Réception 24h/24'), 'icon': 'fa-clock'},
            {'name': _('Service de chambre'), 'icon': 'fa-bell'},
            {'name': _('Blanchisserie'), 'icon': 'fa-soap'},
            {'name': _('Navette aéroport'), 'icon': 'fa-shuttle-van'},
        ]
    },
    {
        'name': _('Installations'),
        'icon': 'fa-building',
        'amenities': [
            {'name': _('Parking'), 'icon': 'fa-parking'},
            {'name': _('Piscine'), 'icon': 'fa-swimming-pool'},
            {'name': _('Salle de sport'), 'icon': 'fa-dumbbell'},
            {'name': _('Ascenseur'), 'icon': 'fa-elevator'},
            {'name': _('Jardin'), 'icon': 'fa-tree'},
        ]
    },
    {
        'name': _('Accessibilité'),
        'icon': 'fa-wheelchair',
        'amenities': [
            {'name': _('Accès handicapé'), 'icon': 'fa-wheelchair'},
            {'name': _('Toilettes PMR'), 'icon': 'fa-restroom'},
        ]
    },
    {
        'name': _('Restauration'),
        'icon': 'fa-utensils',
        'amenities': [
            {'name': _('Restaurant'), 'icon': 'fa-utensils'},
            {'name': _('Bar'), 'icon': 'fa-glass-martini'},
            {'name': _('Petit-déjeuner inclus'), 'icon': 'fa-coffee'},
        ]
    },
    {
        'name': _('Chambre'),
        'icon': 'fa-bed',
        'amenities': [
            {'name': _('Climatisation'), 'icon': 'fa-snowflake'},
            {'name': _('Télévision'), 'icon': 'fa-tv'},
            {'name': _('Coffre-fort'), 'icon': 'fa-lock'},
            {'name': _('Balcon'), 'icon': 'fa-archway'},
        ]
    },
]

class Command(BaseCommand):
    help = 'Initialise les catégories et commodités pour les business (tourisme/hôtellerie)'

    def handle(self, *args, **options):
        created_categories = 0
        created_amenities = 0
        for cat in CATEGORIES:
            category, cat_created = BusinessAmenityCategory.objects.get_or_create(
                name=cat['name'],
                defaults={
                    'description': cat['name'],
                    'icon': cat['icon'],
                    'is_active': True
                }
            )
            if cat_created:
                created_categories += 1
                self.stdout.write(self.style.SUCCESS(f"Catégorie créée : {category.name}"))
            else:
                self.stdout.write(self.style.WARNING(f"Catégorie existante : {category.name}"))
            for amenity in cat['amenities']:
                amenity_obj, amenity_created = BusinessAmenity.objects.get_or_create(
                    name=amenity['name'],
                    category=category,
                    defaults={
                        'description': amenity['name'],
                        'icon': amenity['icon'],
                        'is_active': True
                    }
                )
                if amenity_created:
                    created_amenities += 1
                    self.stdout.write(self.style.SUCCESS(f"  - Commodité créée : {amenity_obj.name}"))
                else:
                    self.stdout.write(self.style.WARNING(f"  - Commodité existante : {amenity_obj.name}"))
        self.stdout.write(self.style.SUCCESS(f"\nTotal catégories créées : {created_categories}"))
        self.stdout.write(self.style.SUCCESS(f"Total commodités créées : {created_amenities}")) 