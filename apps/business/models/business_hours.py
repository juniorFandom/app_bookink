from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.core.models import TimeStampedModel
from .business_location import BusinessLocation

class BusinessHours(TimeStampedModel):
    """
    Model for managing detailed business operating hours
    """
    DAYS_OF_WEEK = [
        (0, _('Monday')),
        (1, _('Tuesday')),
        (2, _('Wednesday')),
        (3, _('Thursday')),
        (4, _('Friday')),
        (5, _('Saturday')),
        (6, _('Sunday')),
    ]

    business_location = models.ForeignKey(
        BusinessLocation,
        on_delete=models.CASCADE,
        related_name='business_hours',
        verbose_name=_('Business Location'),
        null=True,
        blank=True
    )
    day = models.IntegerField(
        _('Day of Week'),
        choices=DAYS_OF_WEEK,
        help_text=_('Day of the week')
    )
    opening_time = models.TimeField(
        _('Opening Time'),
        help_text=_('Time when the business opens')
    )
    closing_time = models.TimeField(
        _('Closing Time'),
        help_text=_('Time when the business closes')
    )
    is_closed = models.BooleanField(
        _('Closed'),
        default=False,
        help_text=_('Whether the business is closed on this day')
    )
    
    # Break time (e.g., lunch break)
    break_start = models.TimeField(
        _('Break Start Time'),
        null=True,
        blank=True,
        help_text=_('Start time of break/siesta (if applicable)')
    )
    break_end = models.TimeField(
        _('Break End Time'),
        null=True,
        blank=True,
        help_text=_('End time of break/siesta (if applicable)')
    )

    class Meta:
        verbose_name = _('Business Hours')
        verbose_name_plural = _('Business Hours')
        ordering = ['business_location', 'day']
        unique_together = ['business_location', 'day']
        indexes = [
            models.Index(fields=['business_location', 'day']),
        ]

    def __str__(self):
        if self.is_closed:
            return f"{self.business_location.name} - {self.get_day_display()} (Closed)"
        return f"{self.business_location.name} - {self.get_day_display()} ({self.opening_time} - {self.closing_time})"

    def clean(self):
        """
        Validate the business hours
        """
        if not self.is_closed:
            if self.closing_time <= self.opening_time:
                raise ValidationError(_('Closing time must be after opening time.'))
            
            if self.break_start and self.break_end:
                if self.break_end <= self.break_start:
                    raise ValidationError(_('Break end time must be after break start time.'))
                if self.break_start < self.opening_time or self.break_end > self.closing_time:
                    raise ValidationError(_('Break times must be within opening hours.'))
            elif bool(self.break_start) != bool(self.break_end):
                raise ValidationError(
                    _('Both break start and end times must be set or neither')
                )

    def is_open_at(self, time=None):
        """
        Check if the business is open at a specific time
        
        Args:
            time (datetime.time, optional): Time to check. Defaults to current time.
        
        Returns:
            bool: True if business is open, False otherwise
        """
        if self.is_closed:
            return False
            
        if time is None:
            time = timezone.localtime().time()
            
        if time < self.opening_time or time >= self.closing_time:
            return False
            
        if self.break_start and self.break_end:
            if self.break_start <= time < self.break_end:
                return False
                
        return True

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

class SpecialBusinessHours(TimeStampedModel):
    """
    Model for managing special operating hours (holidays, events, etc.)
    """
    business_location = models.ForeignKey(
        BusinessLocation,
        on_delete=models.CASCADE,
        related_name='special_business_hours',
        verbose_name=_('Business Location'),
        null=True,
        blank=True
    )
    date = models.DateField(
        _('Date'),
        help_text=_('Date for special hours')
    )
    reason = models.CharField(
        _('Reason'),
        max_length=200,
        help_text=_('Reason for special hours (e.g., Holiday, Event)')
    )
    is_closed = models.BooleanField(
        _('Closed'),
        default=False,
        help_text=_('Whether the business is closed on this date')
    )
    opening_time = models.TimeField(
        _('Opening Time'),
        null=True,
        blank=True,
        help_text=_('Special opening time (blank if closed)')
    )
    closing_time = models.TimeField(
        _('Closing Time'),
        null=True,
        blank=True,
        help_text=_('Special closing time (blank if closed)')
    )

    class Meta:
        verbose_name = _('Special Business Hours')
        verbose_name_plural = _('Special Business Hours')
        ordering = ['business_location', 'date']
        unique_together = ['business_location', 'date']
        indexes = [
            models.Index(fields=['business_location', 'date']),
        ]

    def __str__(self):
        status = "Closed" if self.is_closed else f"{self.opening_time} - {self.closing_time}"
        return f"{self.business_location.name} - {self.date} ({status}): {self.reason}"

    def clean(self):
        """
        Validate the special business hours
        """
        if not self.is_closed:
            if not self.opening_time or not self.closing_time:
                raise ValidationError(_('Opening and closing times are required when not closed.'))
            if self.closing_time <= self.opening_time:
                raise ValidationError(_('Closing time must be after opening time.')) 

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs) 