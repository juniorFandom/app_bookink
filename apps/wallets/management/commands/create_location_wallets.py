from django.core.management.base import BaseCommand
from apps.business.models import BusinessLocation
from apps.wallets.models.wallet import BusinessLocationWallet

class Command(BaseCommand):
    help = 'Crée un wallet pour chaque BusinessLocation sans wallet.'

    def handle(self, *args, **options):
        count = 0
        for location in BusinessLocation.objects.all():
            if not hasattr(location, 'wallet'):
                BusinessLocationWallet.objects.create(business_location=location)
                self.stdout.write(self.style.SUCCESS(f"Wallet créé pour {location.name}"))
                count += 1
        if count == 0:
            self.stdout.write(self.style.WARNING("Tous les établissements ont déjà un wallet."))
        else:
            self.stdout.write(self.style.SUCCESS(f"{count} wallets créés.")) 