from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from apps.rooms.models import RoomImage


class Command(BaseCommand):
    help = 'Nettoie les images temporaires orphelines (room=None) plus anciennes que 24h'

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=1,
            help='Nombre de jours après lesquels supprimer les images temporaires (défaut: 1)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Affiche ce qui serait supprimé sans le faire'
        )

    def handle(self, *args, **options):
        days = options['days']
        dry_run = options['dry_run']
        
        # Calculer la date limite
        cutoff_date = timezone.now() - timedelta(days=days)
        
        # Trouver les images temporaires orphelines
        orphaned_images = RoomImage.objects.filter(
            room=None,
            created_at__lt=cutoff_date
        )
        
        count = orphaned_images.count()
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS('Aucune image temporaire orpheline trouvée.')
            )
            return
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(
                    f'DRY RUN: {count} image(s) temporaire(s) seraient supprimées '
                    f'(créées avant {cutoff_date.strftime("%Y-%m-%d %H:%M")})'
                )
            )
            for img in orphaned_images[:5]:  # Afficher les 5 premières
                self.stdout.write(f'  - {img.image.name} (créée le {img.created_at})')
            if count > 5:
                self.stdout.write(f'  ... et {count - 5} autres')
        else:
            # Supprimer les images
            for img in orphaned_images:
                try:
                    img.image.delete(save=False)
                    img.delete()
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Erreur lors de la suppression de {img.image.name}: {e}')
                    )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'{count} image(s) temporaire(s) supprimée(s) avec succès.'
                )
            ) 