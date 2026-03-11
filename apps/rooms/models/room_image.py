from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models import TimeStampedModel


class RoomImage(TimeStampedModel):
    """
    Model for storing room gallery images.
    """
    room = models.ForeignKey(
        'rooms.Room',
        on_delete=models.CASCADE,
        related_name='images',
        verbose_name=_('Room'),
        null=True,
        blank=True
    )
    image = models.ImageField(_('Image'), upload_to='rooms/galleries/', null=True, blank=True)
    caption = models.CharField(_('Caption'), max_length=255, blank=True, null=True)
    order = models.IntegerField(_('Order'), default=0)

    class Meta:
        verbose_name = _('Room image')
        verbose_name_plural = _('Room images')
        ordering = ['order']

    def __str__(self):
        return f"Image {self.order} for {self.room}" 