"""Guide app forms."""
from django import forms
from django.utils.translation import gettext_lazy as _

from .models import GuideProfile


class GuideProfileForm(forms.ModelForm):
    """Form for creating/updating guide profiles."""

    class Meta:
        model = GuideProfile
        fields = [
            'business_location',
            'license_number',
            'years_of_experience',
            'languages_spoken',
            'specializations',
            'hourly_rate',
            'bio'
        ]
        widgets = {
            'business_location': forms.Select(attrs={
                'class': 'form-control'
            }),
            'license_number': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': _('Enter your guide license number')
            }),
            'years_of_experience': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0'
            }),
            'languages_spoken': forms.SelectMultiple(attrs={
                'class': 'form-control select2',
                'data-placeholder': _('Select languages you speak')
            }),
            'specializations': forms.SelectMultiple(attrs={
                'class': 'form-control select2',
                'data-placeholder': _('Select your specializations')
            }),
            'hourly_rate': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'step': '0.01'
            }),
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': _('Tell us about yourself and your experience')
            })
        }


class GuideVerificationForm(forms.ModelForm):
    """Form for guide verification document upload."""
    
    class Meta:
        model = GuideProfile
        fields = ['verification_document']
        widgets = {
            'verification_document': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': '.pdf,.jpg,.jpeg,.png'
            })
        }

    def clean_verification_document(self):
        document = self.cleaned_data.get('verification_document')
        if document:
            if document.size > 5 * 1024 * 1024:  # 5MB
                raise forms.ValidationError(_('File size must be no more than 5MB.'))
            if not document.content_type in ['application/pdf', 'image/jpeg', 'image/png']:
                raise forms.ValidationError(_('File must be PDF, JPEG or PNG.'))
        return document 