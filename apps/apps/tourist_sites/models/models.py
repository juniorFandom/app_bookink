from django.db import models
from django.conf import settings
from django.urls import reverse

# --- Types de danger statiques ---
DANGER_TYPE_CHOICES = [
    ('sanitaire', 'Risque sanitaire'),
    ('naturel', 'Naturel'),
    ('accident', 'Accident fréquent'),
    ('criminalite', 'Criminalité'),
    ('conflit', 'Conflit'),
    ('autre', 'Autre'),
]

class TouristSiteCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class TouristSite(models.Model):
    name = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(TouristSiteCategory, on_delete=models.SET_NULL, null=True, related_name='sites')
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class TouristSiteImage(models.Model):
    site = models.ForeignKey(TouristSite, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='tourist_sites/')
    caption = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(default=False)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image de {self.site.name}"

class ZoneDangereuse(models.Model):
    class Statut(models.TextChoices):
        SIGNALEE = 'SIGNALEE', 'Signalée'
        VERIFIEE = 'VERIFIEE', 'Vérifiée'
        RESOLUE = 'RESOLUE', 'Résolue'
        REJETEE = 'REJETEE', 'Rejetée'

    id_zonedangereuse = models.AutoField(primary_key=True)
    nom_zone = models.CharField(max_length=200, verbose_name="Nom de la zone")
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name="Latitude")
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True, verbose_name="Longitude")
    image = models.ImageField(upload_to='zones_dangereuses/', null=True, blank=True, verbose_name="Image (optionnelle)")
    guide_rapporteur = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='zones_dangereuses_rapportees', verbose_name="Guide rapporteur"
    )
    type_danger = models.CharField(max_length=20, choices=DANGER_TYPE_CHOICES, verbose_name="Type de danger")
    description_danger = models.TextField(verbose_name="Description du danger")
    statut = models.CharField(max_length=10, choices=Statut.choices, default=Statut.SIGNALEE, verbose_name="Statut")
    date_signalement = models.DateTimeField(auto_now_add=True, verbose_name="Date du signalement")
    site = models.ForeignKey('TouristSite', on_delete=models.CASCADE, related_name='zones_dangereuses', null=True, blank=True, verbose_name="Site touristique concerné")

    def __str__(self):
        return f"{self.nom_zone} ({self.get_statut_display()})"

    def get_likes_count(self):
        return self.votes.filter(is_like=True).count()

    def get_dislikes_count(self):
        return self.votes.filter(is_like=False).count()

    def get_user_vote(self, user):
        try:
            vote = self.votes.get(utilisateur=user)
            return vote.is_like
        except ZoneDangereuseVote.DoesNotExist:
            return None

    def check_validation(self, seuil=3):
        if self.get_likes_count() >= seuil and self.statut == self.Statut.SIGNALEE:
            self.statut = self.Statut.VERIFIEE
            self.save()

    class Meta:
        verbose_name = "Zone Dangereuse"
        verbose_name_plural = "Zones Dangereuses"
        ordering = ['-date_signalement', 'nom_zone']

class ZoneDangereuseVote(models.Model):
    zone = models.ForeignKey(ZoneDangereuse, on_delete=models.CASCADE, related_name='votes', verbose_name="Zone dangereuse")
    utilisateur = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='votes_zones_dangereuses', verbose_name="Utilisateur")
    is_like = models.BooleanField(verbose_name="Vote positif", help_text="True pour like, False pour dislike")
    date_vote = models.DateTimeField(auto_now_add=True, verbose_name="Date du vote")

    def __str__(self):
        vote_type = "Like" if self.is_like else "Dislike"
        return f"{self.utilisateur} - {vote_type} - {self.zone.nom_zone}"

    class Meta:
        verbose_name = "Vote Zone Dangereuse"
        verbose_name_plural = "Votes Zones Dangereuses"
        unique_together = [['zone', 'utilisateur']]
        ordering = ['-date_vote']

# --- Notification interne ---
class Notification(models.Model):
    destinataire = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    url = models.URLField()
    is_read = models.BooleanField(default=False)
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notif à {self.destinataire}: {self.message}" 