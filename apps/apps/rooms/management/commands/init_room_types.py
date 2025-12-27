from django.core.management.base import BaseCommand
from apps.rooms.models.room_type import RoomType
from django.utils.translation import gettext_lazy as _

ROOM_TYPES = [
    {
        'name': _('Chambre Simple'),
        'code': 'SINGLE',
        'description': _('Chambre confortable avec un lit simple, idéale pour un voyageur seul'),
        'max_occupancy': 1,
        'base_price': 25000.00,
        'amenities': [
            'Wi-Fi', 'Climatisation', 'Télévision', 'Salle de bain privée',
            'Serviettes', 'Produits de toilette', 'Café/Thé'
        ]
    },
    {
        'name': _('Chambre Double'),
        'code': 'DOUBLE',
        'description': _('Chambre spacieuse avec un lit double, parfaite pour les couples'),
        'max_occupancy': 2,
        'base_price': 35000.00,
        'amenities': [
            'Wi-Fi', 'Climatisation', 'Télévision', 'Salle de bain privée',
            'Serviettes', 'Produits de toilette', 'Café/Thé', 'Coffre-fort'
        ]
    },
    {
        'name': _('Chambre Twin'),
        'code': 'TWIN',
        'description': _('Chambre avec deux lits simples, idéale pour les amis ou collègues'),
        'max_occupancy': 2,
        'base_price': 35000.00,
        'amenities': [
            'Wi-Fi', 'Climatisation', 'Télévision', 'Salle de bain privée',
            'Serviettes', 'Produits de toilette', 'Café/Thé', 'Coffre-fort'
        ]
    },
    {
        'name': _('Suite Standard'),
        'code': 'SUITE_STD',
        'description': _('Suite élégante avec espace de vie séparé et équipements premium'),
        'max_occupancy': 3,
        'base_price': 55000.00,
        'amenities': [
            'Wi-Fi', 'Climatisation', 'Télévision', 'Salle de bain privée',
            'Serviettes', 'Produits de toilette', 'Café/Thé', 'Coffre-fort',
            'Espace de travail', 'Mini-bar', 'Balcon', 'Vue'
        ]
    },
    {
        'name': _('Suite Familiale'),
        'code': 'SUITE_FAM',
        'description': _('Suite spacieuse avec chambres séparées, parfaite pour les familles'),
        'max_occupancy': 4,
        'base_price': 75000.00,
        'amenities': [
            'Wi-Fi', 'Climatisation', 'Télévision', 'Salle de bain privée',
            'Serviettes', 'Produits de toilette', 'Café/Thé', 'Coffre-fort',
            'Espace de travail', 'Mini-bar', 'Balcon', 'Vue', 'Lit d\'appoint'
        ]
    },
    {
        'name': _('Suite Présidentielle'),
        'code': 'SUITE_PRES',
        'description': _('Suite de luxe avec tous les équipements premium et services VIP'),
        'max_occupancy': 4,
        'base_price': 120000.00,
        'amenities': [
            'Wi-Fi', 'Climatisation', 'Télévision', 'Salle de bain privée',
            'Serviettes', 'Produits de toilette', 'Café/Thé', 'Coffre-fort',
            'Espace de travail', 'Mini-bar', 'Balcon', 'Vue', 'Jacuzzi',
            'Service de conciergerie', 'Accès VIP', 'Parking privé'
        ]
    },
    {
        'name': _('Chambre Accessible'),
        'code': 'ACCESSIBLE',
        'description': _('Chambre adaptée aux personnes à mobilité réduite'),
        'max_occupancy': 2,
        'base_price': 30000.00,
        'amenities': [
            'Wi-Fi', 'Climatisation', 'Télévision', 'Salle de bain adaptée',
            'Serviettes', 'Produits de toilette', 'Café/Thé', 'Accès handicapé',
            'Barres d\'appui', 'Douche accessible'
        ]
    },
    {
        'name': _('Chambre Économique'),
        'code': 'ECONOMIC',
        'description': _('Chambre simple et confortable à prix abordable'),
        'max_occupancy': 1,
        'base_price': 18000.00,
        'amenities': [
            'Wi-Fi', 'Ventilateur', 'Télévision', 'Salle de bain privée',
            'Serviettes', 'Produits de toilette'
        ]
    }
]

class Command(BaseCommand):
    help = 'Initialise les types de chambres pour l\'hôtellerie'

    def handle(self, *args, **options):
        created_room_types = 0
        updated_room_types = 0
        
        for room_type_data in ROOM_TYPES:
            room_type, created = RoomType.objects.get_or_create(
                code=room_type_data['code'],
                defaults={
                    'name': room_type_data['name'],
                    'description': room_type_data['description'],
                    'max_occupancy': room_type_data['max_occupancy'],
                    'base_price': room_type_data['base_price'],
                    'amenities': room_type_data['amenities'],
                    'is_active': True
                }
            )
            
            if created:
                created_room_types += 1
                self.stdout.write(
                    self.style.SUCCESS(f"Type de chambre créé : {room_type.name} ({room_type.code})")
                )
            else:
                # Mettre à jour les données existantes
                room_type.name = room_type_data['name']
                room_type.description = room_type_data['description']
                room_type.max_occupancy = room_type_data['max_occupancy']
                room_type.base_price = room_type_data['base_price']
                room_type.amenities = room_type_data['amenities']
                room_type.is_active = True
                room_type.save()
                updated_room_types += 1
                self.stdout.write(
                    self.style.WARNING(f"Type de chambre mis à jour : {room_type.name} ({room_type.code})")
                )
        
        self.stdout.write(self.style.SUCCESS(f"\nRésumé :"))
        self.stdout.write(self.style.SUCCESS(f"- Types de chambres créés : {created_room_types}"))
        self.stdout.write(self.style.SUCCESS(f"- Types de chambres mis à jour : {updated_room_types}"))
        self.stdout.write(self.style.SUCCESS(f"- Total : {created_room_types + updated_room_types}"))
        
        # Note sur les images
        self.stdout.write(self.style.NOTICE(
            "\nNote : Les images des types de chambres ne sont pas incluses dans cette initialisation. "
            "Vous pouvez les ajouter manuellement via l'interface d'administration ou créer "
            "un script séparé pour gérer les images."
        )) 