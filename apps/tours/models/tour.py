from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.business.models import BusinessLocation
from django.utils.text import slugify
import datetime

class Tour(models.Model):
    business_location = models.ForeignKey(
        BusinessLocation,
        on_delete=models.CASCADE,
        verbose_name=_('Business Location'),
        related_name='tours'
    )
    nom_balade = models.CharField(_('Nom de la balade'), max_length=255, default='Tour sans nom')
    description = models.TextField(_('Description'))
    type = models.CharField(_('Type'), max_length=100, default='autre')
    duree = models.IntegerField(_('Durée (minutes)'), default=60)
    image = models.ImageField(_('Image'), upload_to='tours/images/', default='default.jpg', blank=True)
    point_rencontre_longitude = models.FloatField(_('Longitude du point de rencontre'), default=0)
    point_rencontre_latitude = models.FloatField(_('Latitude du point de rencontre'), default=0)
    exigence = models.CharField(_('Exigence'), max_length=255, default='', blank=True)
    nombre_participant_min = models.IntegerField(_('Nombre de participants min'), default=1)
    nombre_participant_max = models.IntegerField(_('Nombre de participants max'), default=1)
    prix_par_personne = models.DecimalField(_('Prix par personne'), max_digits=10, decimal_places=2, default=0)
    is_active = models.BooleanField(_('Actif'), default=True)
    date_debut = models.DateField(_('Date de début'), default=datetime.date.today)
    heure_depart = models.TimeField(_('Heure de départ'), default=datetime.time(9, 0))
    slug = models.SlugField(_('Slug'), max_length=255, unique=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Tour')
        verbose_name_plural = _('Tours')
        ordering = ['-date_debut', '-heure_depart']

    def __str__(self):
        return self.nom_balade

    def save(self, *args, **kwargs):
        if not self.slug and self.nom_balade:
            self.slug = slugify(self.nom_balade)
        super().save(*args, **kwargs) 