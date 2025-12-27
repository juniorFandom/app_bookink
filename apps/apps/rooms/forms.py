from django import forms
from django.utils.translation import gettext_lazy as _
from .models import Room, RoomType, RoomBooking, RoomImage


class RoomTypeForm(forms.ModelForm):
    """Form for creating and updating room types."""
    
    class Meta:
        model = RoomType
        fields = [
            'name', 'code', 'description', 'max_occupancy',
            'base_price', 'amenities', 'image'
        ]
        widgets = {
            'amenities': forms.Textarea(attrs={'rows': 3}),
        }


class RoomForm(forms.ModelForm):
    """Form for creating and updating rooms."""
    
    class Meta:
        model = Room
        fields = [
            'room_type', 'room_number', 'floor', 'description',
            'price_per_night', 'max_occupancy', 'amenities',
            'is_available', 'maintenance_mode'
        ]
        widgets = {
            'amenities': forms.Textarea(attrs={'rows': 3}),
        }


class RoomImageForm(forms.ModelForm):
    """Form for uploading room images."""
    
    class Meta:
        model = RoomImage
        fields = ['image', 'caption', 'order']
        widgets = {
            'caption': forms.TextInput(attrs={'placeholder': _('Optional caption for the image')}),
            'order': forms.NumberInput(attrs={'min': 0}),
        }


class RoomSearchForm(forms.Form):
    """Form for searching rooms."""
    check_in_date = forms.DateField(
        label=_('Check-in date'),
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False
    )
    check_out_date = forms.DateField(
        label=_('Check-out date'),
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=False
    )
    guests = forms.IntegerField(
        label=_('Number of guests'),
        min_value=1,
        initial=1,
        required=False
    )
    room_type = forms.ModelChoiceField(
        label=_('Room type'),
        queryset=RoomType.objects.filter(is_active=True),
        required=False
    )


class RoomBookingForm(forms.ModelForm):
    """Form for room bookings."""
    check_in_date = forms.DateField(
        label=_('Date d\'arrivée'),
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=True
    )
    check_out_date = forms.DateField(
        label=_('Date de départ'),
        widget=forms.DateInput(attrs={'type': 'date'}),
        required=True
    )
    class Meta:
        model = RoomBooking
        fields = [
            'check_in_date', 'check_out_date',
            'adults_count', 'children_count',
            'hotel_notes'
        ]
        widgets = {
            'hotel_notes': forms.Textarea(attrs={'rows': 3}),
        }


class RoomFilterForm(forms.Form):
    """Form for filtering rooms in admin or management interface."""
    room_type = forms.ModelChoiceField(
        label=_('Room Type'),
        queryset=RoomType.objects.filter(is_active=True),
        required=False
    )
    is_available = forms.ChoiceField(
        label=_('Availability'),
        choices=[
            ('', _('All')),
            ('true', _('Available')),
            ('false', _('Not Available')),
        ],
        required=False
    )
    maintenance_mode = forms.ChoiceField(
        label=_('Maintenance'),
        choices=[
            ('', _('All')),
            ('true', _('Under Maintenance')),
            ('false', _('Not Under Maintenance')),
        ],
        required=False
    )
    price_min = forms.DecimalField(
        label=_('Minimum Price'),
        required=False,
        min_value=0
    )
    price_max = forms.DecimalField(
        label=_('Maximum Price'),
        required=False,
        min_value=0
    ) 