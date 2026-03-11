from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.core.models.base import TimeStampedModel
from .tour import Tour

class TourSchedule(TimeStampedModel):
    """
    Model representing a scheduled tour.
    """
    tour = models.ForeignKey(
        Tour,
        on_delete=models.CASCADE,
        related_name='tour_schedules',
        verbose_name=_('Tour')
    )
    
    start_datetime = models.DateTimeField(
        verbose_name=_('Start Date and Time')
    )
    
    end_datetime = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('End Date and Time')
    )
    
    available_spots = models.IntegerField(
        verbose_name=_('Available Spots')
    )
    
    price_override = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_('Price Override')
    )
    
    status = models.CharField(
        max_length=20,
        choices=[
            ('SCHEDULED', 'Scheduled'),
            ('CONFIRMED', 'Confirmed'),
            ('CANCELLED', 'Cancelled'),
            ('COMPLETED', 'Completed')
        ],
        default='SCHEDULED'
    )
    
    cancellation_reason = models.TextField(
        null=True,
        blank=True,
        verbose_name=_('Cancellation Reason')
    )

    def __str__(self):
        return f"{self.tour} from {self.start_datetime} to {self.end_datetime} - {self.status}"