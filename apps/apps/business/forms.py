from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .models import (
    Business,
    BusinessLocation,
    BusinessLocationImage,
    BusinessHours,
    BusinessReview,
    BusinessAmenityCategory,
    BusinessAmenity,
    BusinessAmenityAssignment,
    BusinessPermission,
    PermissionRequest
)

class BusinessForm(forms.ModelForm):
    """
    Form for creating and updating business profiles
    """
    class Meta:
        model = Business
        fields = [
            'name',
            'email',
            'phone',
            'website',
            'description',
            'founded_date',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'founded_date': forms.DateInput(attrs={'type': 'date'}),
        }

class BusinessLocationForm(forms.ModelForm):
    """
    Form for creating and updating business locations
    """
    class Meta:
        model = BusinessLocation
        fields = [
            'name',
            'business_location_type',
            'phone',
            'email',
            'registration_number',
            'description',
            'founded_date',
            'is_main_location',
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'founded_date': forms.DateInput(attrs={'type': 'date'}),
        }

class BusinessLocationImageForm(forms.ModelForm):
    """
    Form for uploading business location images
    """
    class Meta:
        model = BusinessLocationImage
        fields = ['image', 'caption', 'is_primary']



class BusinessHoursForm(forms.ModelForm):
    """
    Form for setting business operating hours
    """
    class Meta:
        model = BusinessHours
        fields = [
            'day',
            'opening_time',
            'closing_time',
            'is_closed',
            'break_start',
            'break_end',
        ]
        widgets = {
            'opening_time': forms.TimeInput(attrs={'type': 'time'}),
            'closing_time': forms.TimeInput(attrs={'type': 'time'}),
            'break_start': forms.TimeInput(attrs={'type': 'time'}),
            'break_end': forms.TimeInput(attrs={'type': 'time'}),
        }

class BusinessReviewForm(forms.ModelForm):
    """
    Form for submitting business reviews
    """
    class Meta:
        model = BusinessReview
        fields = [
            'content',
            'service_rating',
            'value_rating',
            'cleanliness_rating',
            'location_rating',
            'visit_date',
            'visit_type',
        ]
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4}),
            'visit_date': forms.DateInput(attrs={'type': 'date'}),
            'service_rating': forms.NumberInput(attrs={'min': 1, 'max': 5}),
            'value_rating': forms.NumberInput(attrs={'min': 1, 'max': 5}),
            'cleanliness_rating': forms.NumberInput(attrs={'min': 1, 'max': 5}),
            'location_rating': forms.NumberInput(attrs={'min': 1, 'max': 5}),
        }

    def clean(self):
        cleaned_data = super().clean()
        visit_date = cleaned_data.get('visit_date')
        
        if visit_date and visit_date > timezone.now().date():
            raise forms.ValidationError({
                'visit_date': _('Visit date cannot be in the future')
            })
        
        return cleaned_data

class BusinessAmenityCategoryForm(forms.ModelForm):
    """
    Form for managing business amenity categories
    """
    class Meta:
        model = BusinessAmenityCategory
        fields = ['name', 'description', 'icon', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class BusinessAmenityForm(forms.ModelForm):
    """
    Form for managing business amenities
    """
    class Meta:
        model = BusinessAmenity
        fields = ['category', 'name', 'description', 'icon', 'is_active']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
        }

class BusinessAmenityAssignmentForm(forms.ModelForm):
    """
    Form for assigning amenities to businesses
    """
    class Meta:
        model = BusinessAmenityAssignment
        fields = ['amenity', 'details', 'is_active']
        widgets = {
            'details': forms.Textarea(attrs={'rows': 3}),
        }

class BusinessSearchForm(forms.Form):
    """
    Form for searching businesses
    """
    SORT_CHOICES = [
        ('name', _('Name')),
        ('rating', _('Rating')),
        ('reviews', _('Number of Reviews')),
        ('distance', _('Distance')),
    ]

    query = forms.CharField(
        label=_('Search'),
        required=False,
        widget=forms.TextInput(attrs={
            'placeholder': _('Search by name, location, or business type...')
        })
    )
    business_type = forms.ChoiceField(
        label=_('Business Type'),
        choices=[('', _('All Types'))] + BusinessLocation.BUSINESS_TYPES,
        required=False
    )
    rating = forms.ChoiceField(
        label=_('Minimum Rating'),
        choices=[
            ('', _('Any Rating')),
            ('4', _('4+ Stars')),
            ('3', _('3+ Stars')),
            ('2', _('2+ Stars')),
        ],
        required=False
    )
    sort_by = forms.ChoiceField(
        label=_('Sort By'),
        choices=SORT_CHOICES,
        required=False,
        initial='name'
    )
    verified_only = forms.BooleanField(
        label=_('Verified Businesses Only'),
        required=False
    )

class BusinessPermissionForm(forms.ModelForm):
    """
    Form for creating and updating business permissions
    """
    class Meta:
        model = BusinessPermission
        fields = [
            'user',
            'permission_type',
            'expires_at',
            'notes',
        ]
        widgets = {
            'expires_at': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-control'
                }
            ),
            'notes': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        business_location = kwargs.pop('business_location', None)
        super().__init__(*args, **kwargs)
        
        if business_location:
            # Filter permission types based on business type
            if business_location.business_location_type == 'hotel':
                self.fields['permission_type'].choices = [
                    choice for choice in BusinessPermission.PERMISSION_TYPES
                    if choice[0] in ['manage_rooms', 'manage_bookings', 'manage_reviews', 'manage_hours', 'manage_amenities', 'manage_images', 'view_analytics', 'full_access']
                ]
            elif business_location.business_location_type == 'restaurant':
                self.fields['permission_type'].choices = [
                    choice for choice in BusinessPermission.PERMISSION_TYPES
                    if choice[0] in ['manage_menu', 'manage_orders', 'manage_reviews', 'manage_hours', 'manage_amenities', 'manage_images', 'view_analytics', 'full_access']
                ]
            elif business_location.business_location_type == 'transport':
                self.fields['permission_type'].choices = [
                    choice for choice in BusinessPermission.PERMISSION_TYPES
                    if choice[0] in ['manage_vehicles', 'manage_bookings', 'manage_reviews', 'manage_hours', 'manage_amenities', 'manage_images', 'view_analytics', 'full_access']
                ]
            elif business_location.business_location_type == 'tour_operator':
                self.fields['permission_type'].choices = [
                    choice for choice in BusinessPermission.PERMISSION_TYPES
                    if choice[0] in ['manage_tours', 'manage_bookings', 'manage_reviews', 'manage_hours', 'manage_amenities', 'manage_images', 'view_analytics', 'full_access']
                ]


class PermissionRequestForm(forms.ModelForm):
    """
    Form for requesting permissions
    """
    class Meta:
        model = PermissionRequest
        fields = [
            'business_location',
            'permission_type',
            'requested_expires_at',
        ]
        widgets = {
            'requested_expires_at': forms.DateTimeInput(
                attrs={
                    'type': 'datetime-local',
                    'class': 'form-control'
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        if user:
            # Filter business locations where user is not the owner
            self.fields['business_location'].queryset = BusinessLocation.objects.filter(
                is_active=True
            ).exclude(
                business__owner=user
            )


class UserSearchForm(forms.Form):
    """
    Form for searching users to assign permissions
    """
    search = forms.CharField(
        max_length=100,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by username, email, or full name...'
        })
    )
    
    def clean_search(self):
        search = self.cleaned_data.get('search')
        if search and len(search.strip()) < 2:
            raise forms.ValidationError('Search term must be at least 2 characters long.')
        return search.strip() if search else ''


class PermissionReviewForm(forms.Form):
    """
    Form for reviewing permission requests
    """
    action = forms.ChoiceField(
        choices=[
            ('approve', 'Approve'),
            ('reject', 'Reject'),
        ],
        widget=forms.RadioSelect
    )
    
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False,
        help_text='Optional notes about your decision'
    ) 