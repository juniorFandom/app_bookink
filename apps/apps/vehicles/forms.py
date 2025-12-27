from django import forms
from django.utils.translation import gettext_lazy as _
from .models import (
    VehicleCategory,
    Vehicle,
    VehicleImage,
    Driver,
    VehicleBooking
)


class VehicleCategoryForm(forms.ModelForm):
    """Form for creating and updating vehicle categories."""
    
    class Meta:
        model = VehicleCategory
        fields = ['name', 'code', 'description', 'icon', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }


class VehicleForm(forms.ModelForm):
    """Form for creating and updating vehicles."""
    
    class Meta:
        model = Vehicle
        fields = [
            'business_location',
            'vehicle_category',
            'make',
            'model',
            'year',
            'license_plate',
            'color',
            'passenger_capacity',
            'transmission',
            'fuel_type',
            'daily_rate',
            'description',
            'main_image',
            'is_available'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'year': forms.NumberInput(attrs={'min': 1900, 'max': 2100}),
            'passenger_capacity': forms.NumberInput(attrs={'min': 1}),
            'daily_rate': forms.NumberInput(attrs={'min': 0}),
        }

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data


class VehicleImageForm(forms.ModelForm):
    """Form for adding images to a vehicle."""
    
    class Meta:
        model = VehicleImage
        fields = ['vehicle', 'image', 'caption', 'order']


class DriverForm(forms.ModelForm):
    """Form for creating and updating drivers."""
    
    class Meta:
        model = Driver
        fields = [
            'business_location',
            'user',
            'first_name',
            'last_name',
            'gender',
            'date_of_birth',
            'phone_number',
            'email',
            'address',
            'license_number',
            'license_type',
            'license_expiry',
            'photo',
            'years_of_experience',
            'languages_spoken',
            'daily_rate',
            'verification_document',
            'is_available',
            'is_verified',
            'notes'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'license_expiry': forms.DateInput(attrs={'type': 'date'}),
            'address': forms.Textarea(attrs={'rows': 3}),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'years_of_experience': forms.NumberInput(attrs={'min': 0}),
            'daily_rate': forms.NumberInput(attrs={'min': 0}),
            'languages_spoken': forms.Textarea(attrs={'rows': 2}),
        }


class VehicleBookingForm(forms.ModelForm):
    """Form for creating and updating vehicle bookings."""
    with_driver = forms.BooleanField(label=_('Avec chauffeur'), required=False, initial=False)

    class Meta:
        model = VehicleBooking
        fields = [
            'vehicle',
            'customer',
            'pickup_datetime',
            'return_datetime',
            'pickup_location',
            'return_location',
            'daily_rate',
            'driver_fee',
            'additional_charges',
            'notes',
            'terms_accepted',
            'with_driver',
        ]
        widgets = {
            'pickup_datetime': forms.DateTimeInput(
                attrs={'type': 'datetime-local'}
            ),
            'return_datetime': forms.DateTimeInput(
                attrs={'type': 'datetime-local'}
            ),
            'notes': forms.Textarea(attrs={'rows': 3}),
            'daily_rate': forms.NumberInput(attrs={'min': 0, 'readonly': 'readonly'}),
            'driver_fee': forms.NumberInput(attrs={'min': 0}),
            'additional_charges': forms.NumberInput(attrs={'min': 0}),
            'pickup_location': forms.TextInput(),
            'return_location': forms.TextInput(),
        }

    def __init__(self, *args, **kwargs):
        vehicle = kwargs.pop('vehicle', None)
        super().__init__(*args, **kwargs)
        if vehicle:
            self.fields['vehicle'].initial = vehicle.pk
            self.fields['pickup_location'].initial = vehicle.business_location.name
            self.fields['return_location'].initial = vehicle.business_location.name
            self.fields['daily_rate'].initial = vehicle.daily_rate
            self.driver_daily_rate = getattr(vehicle, 'driver_daily_rate', 0)
            self.fields['driver_fee'].initial = 0
        
        # Hide fields that should not be visible to users
        self.fields['vehicle'].widget = forms.HiddenInput()
        self.fields['customer'].widget = forms.HiddenInput()
        if 'driver' in self.fields:
            self.fields['driver'].widget = forms.HiddenInput()

    def clean(self):
        cleaned_data = super().clean()
        with_driver = cleaned_data.get('with_driver')
        driver_fee = getattr(self, 'driver_daily_rate', 0)
        if with_driver:
            cleaned_data['driver_fee'] = driver_fee
        else:
            cleaned_data['driver_fee'] = 0
        return cleaned_data


class VehicleSearchForm(forms.Form):
    """Form for searching available vehicles."""
    
    pickup_datetime = forms.DateTimeField(
        label=_('Pickup Date and Time'),
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'})
    )
    return_datetime = forms.DateTimeField(
        label=_('Return Date and Time'),
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'})
    )
    category = forms.ModelChoiceField(
        label=_('Vehicle Category'),
        queryset=VehicleCategory.objects.filter(is_active=True),
        required=False
    )
    passenger_capacity = forms.IntegerField(
        label=_('Minimum Passenger Capacity'),
        required=False,
        min_value=1
    )
    transmission = forms.ChoiceField(
        label=_('Transmission'),
        choices=[('', '-----')] + Vehicle.TRANSMISSION_CHOICES,
        required=False
    )
    max_daily_rate = forms.DecimalField(
        label=_('Maximum Daily Rate'),
        required=False,
        min_value=0
    )

    def clean(self):
        cleaned_data = super().clean()
        pickup_datetime = cleaned_data.get('pickup_datetime')
        return_datetime = cleaned_data.get('return_datetime')

        if pickup_datetime and return_datetime and pickup_datetime >= return_datetime:
            raise forms.ValidationError(
                _('Return datetime must be after pickup datetime.')
            )

        return cleaned_data 