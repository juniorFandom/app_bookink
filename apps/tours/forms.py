from django import forms
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from .models import (
    Tour,
    TourDestination,
    TourDestinationImage,
    TourBooking,
    TourSchedule,
    TourReview
)


class TourForm(forms.ModelForm):
    """Form for creating and updating tours."""
    class Meta:
        model = Tour
        fields = [
            'business_location',
            'nom_balade',
            'slug',
            'description',
            'type',
            'duree',
            'image',
            'point_rencontre_longitude',
            'point_rencontre_latitude',
            'exigence',
            'nombre_participant_min',
            'nombre_participant_max',
            'prix_par_personne',
            'is_active',
            'date_debut',
            'heure_depart',
        ]
        widgets = {
            'business_location': forms.HiddenInput(),
            'slug': forms.HiddenInput(),
            'description': forms.Textarea(attrs={'rows': 4}),
            'duree': forms.NumberInput(attrs={'min': 1}),
            'nombre_participant_min': forms.NumberInput(attrs={'min': 1}),
            'nombre_participant_max': forms.NumberInput(attrs={'min': 1}),
            'prix_par_personne': forms.NumberInput(attrs={'min': 0}),
            'date_debut': forms.DateInput(attrs={'type': 'date'}),
            'heure_depart': forms.TimeInput(attrs={'type': 'time'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ajouter les classes Bootstrap à tous les champs
        for field_name, field in self.fields.items():
            if field_name not in ['is_active', 'business_location', 'slug']:  # Ne pas ajouter form-control aux champs cachés et checkboxes
                field.widget.attrs.update({'class': 'form-control'})
            elif field_name == 'is_active':
                field.widget.attrs.update({'class': 'form-check-input'})
        
        # Rendre le slug optionnel pour la création
        if not self.instance.pk:
            self.fields['slug'].required = False

    def clean(self):
        cleaned_data = super().clean()
        min_participants = cleaned_data.get('nombre_participant_min')
        max_participants = cleaned_data.get('nombre_participant_max')
        
        if min_participants is not None and max_participants is not None:
            if min_participants > max_participants:
                raise forms.ValidationError(_('Le nombre minimum de participants ne peut pas être supérieur au maximum.'))
        
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        # Le slug sera généré automatiquement par la méthode save() du modèle
        if commit:
            instance.save()
        return instance


class TourDestinationForm(forms.ModelForm):
    """Form for creating and updating tour destinations."""
    
    class Meta:
        model = TourDestination
        fields = [
            'tour',
            'name',
            'slug',
            'description',
            'city',
            'region',
            'country',
            'postal_code',
            'latitude',
            'longitude',
            'day_number',
            'duration',
            'highlights',
            'features',
            'best_time_to_visit',
            'climate',
            'how_to_get_there',
            'is_active',
            'is_featured'
        ]
        widgets = {
            'slug': forms.HiddenInput(),
            'description': forms.Textarea(attrs={'rows': 4}),
            'highlights': forms.Textarea(attrs={'rows': 3}),
            'features': forms.Textarea(attrs={'rows': 3}),
            'climate': forms.Textarea(attrs={'rows': 3}),
            'how_to_get_there': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make slug optional for new destinations
        if not self.instance.pk:
            self.fields['slug'].required = False
        
        for field_name, field in self.fields.items():
            if field_name not in ['is_active', 'is_featured', 'slug']:
                field.widget.attrs.update({'class': 'form-control'})
            elif field_name in ['is_active', 'is_featured']:
                field.widget.attrs.update({'class': 'form-check-input'})


class TourDestinationImageForm(forms.ModelForm):
    """Form for uploading destination images."""
    
    class Meta:
        model = TourDestinationImage
        fields = ['image', 'caption', 'order']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})


class TourBookingForm(forms.ModelForm):
    """Form for creating tour bookings."""
    
    # Champs supplémentaires pour le formulaire
    first_name = forms.CharField(
        label=_('First Name'),
        max_length=100,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    email = forms.EmailField(
        label=_('Email'),
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )
    special_requirements = forms.CharField(
        label=_('Special Requirements'),
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'})
    )
    total_amount = forms.CharField(
        label=_('Total Amount'),
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'readonly': 'readonly',
            'style': 'background-color: #f8f9fa; font-weight: bold; color: #2563eb;'
        })
    )
    
    payment_percentage = forms.ChoiceField(
        label=_('Payment Percentage'),
        choices=[
            ('20', '20% - Acompte'),
            ('50', '50% - Demi-paiement'),
            ('100', '100% - Paiement complet')
        ],
        initial='100',
        widget=forms.RadioSelect(attrs={'class': 'payment-percentage-radio'})
    )
    
    class Meta:
        model = TourBooking
        fields = [
            'number_of_participants',
            'guide_notes'
        ]
        widgets = {
            'number_of_participants': forms.NumberInput(attrs={'class': 'form-control', 'min': 1}),
            'guide_notes': forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        self.tour = kwargs.pop('tour', None)
        super().__init__(*args, **kwargs)
        
        # Limiter le nombre de participants selon les places disponibles
        if self.tour:
            max_participants = min(self.tour.max_participants, 20)  # Limite raisonnable
            self.fields['number_of_participants'].widget.attrs.update({
                'max': max_participants,
                'min': self.tour.min_participants
            })
            self.fields['number_of_participants'].label = f"{_('Number of Participants')} (max: {max_participants})"

    def clean(self):
        cleaned_data = super().clean()
        number_of_participants = cleaned_data.get('number_of_participants')

        if self.tour and number_of_participants:
            if number_of_participants < self.tour.min_participants:
                raise forms.ValidationError(
                    _('Minimum %(min)d participants required.') % {
                        'min': self.tour.min_participants
                    }
                )
            if number_of_participants > self.tour.max_participants:
                raise forms.ValidationError(
                    _('Maximum %(max)d participants allowed.') % {
                        'max': self.tour.max_participants
                    }
                )

        # Ignorer la validation du champ total_amount car il est calculé côté serveur
        if 'total_amount' in cleaned_data:
            del cleaned_data['total_amount']

        return cleaned_data


class TourScheduleForm(forms.ModelForm):
    """Form for creating and updating tour schedules."""
    
    class Meta:
        model = TourSchedule
        fields = [
            'tour',
            'start_datetime',
            'end_datetime',
            'available_spots',
            'price_override',
            'status',
            'cancellation_reason'
        ]
        widgets = {
            'start_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_datetime': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'cancellation_reason': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})

    def clean(self):
        cleaned_data = super().clean()
        tour_schedule = cleaned_data.get('tour_schedule')

        if tour_schedule:
            if tour_schedule.start_datetime < timezone.now():
                raise forms.ValidationError(_('Start datetime cannot be in the past.'))
            if tour_schedule.end_datetime <= tour_schedule.start_datetime:
                raise forms.ValidationError(_('End datetime must be after start datetime.'))

        return cleaned_data


class TourReviewForm(forms.ModelForm):
    """Form for submitting tour reviews."""
    
    class Meta:
        model = TourReview
        fields = [
            'tour',
            'content',
            'rating',
            'guide_rating',
            'value_rating',
            'activities_rating',
            'transportation_rating',
            'accommodation_rating',
            'food_rating',
            'pros',
            'cons',
            'tips',
            'would_recommend'
        ]
        widgets = {
            'content': forms.Textarea(attrs={'rows': 4}),
            'pros': forms.Textarea(attrs={'rows': 3}),
            'cons': forms.Textarea(attrs={'rows': 3}),
            'tips': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name != 'would_recommend':
                field.widget.attrs.update({'class': 'form-control'})
            else:
                field.widget.attrs.update({'class': 'form-check-input'})


class TourSearchForm(forms.Form):
    """Form for searching tours."""
    query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'placeholder': _('Search tours...')})
    )
    tour_type = forms.ChoiceField(
        required=False,
        choices=[
            ('', _('All Types')),
            ('culturel', _('Culturel')),
            ('aventure', _('Aventure')),
            ('nature', _('Nature')),
            ('autre', _('Autre'))
        ]
    )
    min_price = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2
    )
    max_price = forms.DecimalField(
        required=False,
        min_value=0,
        decimal_places=2
    )
    min_duration = forms.IntegerField(
        required=False,
        min_value=1
    )
    max_duration = forms.IntegerField(
        required=False,
        min_value=1
    )
    min_rating = forms.ChoiceField(
        required=False,
        choices=[
            ('', _('Any Rating')),
            ('4', _('4+ Stars')),
            ('3', _('3+ Stars')),
            ('2', _('2+ Stars')),
            ('1', _('1+ Stars'))
        ]
    )
    sort_by = forms.ChoiceField(
        required=False,
        choices=[
            ('name', _('Name')),
            ('price', _('Price')),
            ('duration', _('Duration')),
            ('rating', _('Rating'))
        ]
    )
    verified_only = forms.BooleanField(
        required=False,
        initial=False,
        label=_('Verified Tours Only')
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if field_name != 'verified_only':
                field.widget.attrs.update({'class': 'form-control'})
            else:
                field.widget.attrs.update({'class': 'form-check-input'})

    def clean(self):
        cleaned_data = super().clean()
        # Add any additional validation logic here if needed
        return cleaned_data