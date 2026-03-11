from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.urls import reverse
from .models import ZoneDangereuse, Notification
from django.contrib.auth import get_user_model

User = get_user_model()

@receiver(post_save, sender=ZoneDangereuse)
def notify_users_same_city(sender, instance, created, **kwargs):
    if created:
        ville = instance.guide_rapporteur.ville if instance.guide_rapporteur and instance.guide_rapporteur.ville else "Bandjoun"
        # Notifier tous les utilisateurs de la même ville sauf l'auteur
        destinataires = User.objects.filter(ville=ville).exclude(id=instance.guide_rapporteur_id)
        url = reverse('tourist_sites:zone_dangereuse_detail', args=[instance.id_zonedangereuse])
        for user in destinataires:
            Notification.objects.create(
                destinataire=user,
                message=f"Nouvelle zone dangereuse ajoutée : {instance.nom_zone}",
                url=url
            ) 