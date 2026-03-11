from django import forms
from apps.tourist_sites.models import TouristSite, TouristSiteCategory, TouristSiteImage, ZoneDangereuse, ZoneDangereuseImage


class TouristSiteForm(forms.ModelForm):
    """Formulaire pour créer/modifier un site touristique"""
    
    class Meta:
        model = TouristSite
        fields = ['name', 'description', 'category', 'latitude', 'longitude', 'is_active']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom du site touristique'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Description détaillée du site'
            }),
            'category': forms.Select(attrs={
                'class': 'form-select'
            }),
            'latitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.000001',
                'placeholder': 'Latitude (ex: 48.8584)'
            }),
            'longitude': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.000001',
                'placeholder': 'Longitude (ex: 2.2945)'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


class TouristSiteCategoryForm(forms.ModelForm):
    """Formulaire pour créer/modifier une catégorie"""
    
    class Meta:
        model = TouristSiteCategory
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nom de la catégorie'
            }),
            'description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Description de la catégorie'
            }),
        }


class TouristSiteImageForm(forms.ModelForm):
    """Formulaire pour ajouter des images à un site"""
    
    class Meta:
        model = TouristSiteImage
        fields = ['image', 'caption', 'is_primary']
        widgets = {
            'image': forms.FileInput(attrs={
                'class': 'form-control',
                'accept': 'image/*'
            }),
            'caption': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Légende de l\'image'
            }),
            'is_primary': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }


class TouristSiteSearchForm(forms.Form):
    """Formulaire de recherche pour les sites touristiques"""
    
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Rechercher un site...'
        })
    )
    
    category = forms.ModelChoiceField(
        queryset=TouristSiteCategory.objects.all(),
        required=False,
        empty_label="Toutes les catégories",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    status = forms.ChoiceField(
        choices=[
            ('', 'Tous les statuts'),
            ('active', 'Actifs'),
            ('inactive', 'Inactifs'),
        ],
        required=False,
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )


class ZoneDangereuseForm(forms.ModelForm):
    class Meta:
        model = ZoneDangereuse
        fields = ['nom_zone', 'type_danger', 'description_danger', 'latitude', 'longitude', 'site']
        widgets = {
            'nom_zone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom de la zone'}),
            'type_danger': forms.Select(attrs={'class': 'form-select'}),
            'description_danger': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Décris le danger…'}),
            'latitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001', 'placeholder': 'Latitude'}),
            'longitude': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.000001', 'placeholder': 'Longitude'}),
            'site': forms.Select(attrs={'class': 'form-select'}),
        }


ZoneDangereuseImageFormSet = forms.inlineformset_factory(
    ZoneDangereuse, ZoneDangereuseImage,
    form=ZoneDangereuseImageForm,
    extra=3, can_delete=True
) 