from django import forms
from django.utils.translation import gettext_lazy as _

from .models import FoodCategory, MenuItem, MenuItemImage, RestaurantOrder, OrderItem
from apps.users.models.user import User


class FoodCategoryForm(forms.ModelForm):
    """Form for creating and editing food categories."""
    class Meta:
        model = FoodCategory
        fields = '__all__'


class MenuItemForm(forms.ModelForm):
    """Form for creating and editing menu items."""
    
    additional_images = forms.FileField(
        label=_('Additional Images'),
        required=False,
        widget=forms.ClearableFileInput(attrs={'allow_multiple_selected': True}),
        help_text=_('You can select multiple images')
    )

    replace_images = forms.BooleanField(
        label=_('Replace existing images'),
        required=False,
        initial=False,
        help_text=_('Check this to remove existing images when uploading new ones')
    )

    class Meta:
        model = MenuItem
        exclude = ['slug', 'ingredients', 'allergens', 'calories']


class MenuItemImageForm(forms.ModelForm):
    """Form for adding images to menu items."""
    class Meta:
        model = MenuItemImage
        fields = ['image', 'caption', 'order']
        widgets = {
            'caption': forms.TextInput(attrs={'placeholder': _('Optional caption')}),
            'order': forms.NumberInput(attrs={'min': 0}),
        }


class OrderItemForm(forms.ModelForm):
    """Form for adding items to an order."""

    class Meta:
        model = OrderItem
        fields = ['menu_item', 'quantity', 'special_instructions']
        widgets = {
            'quantity': forms.NumberInput(attrs={'min': 1}),
            'special_instructions': forms.Textarea(attrs={'rows': 2}),
        }

    def __init__(self, *args, business_location=None, **kwargs):
        super().__init__(*args, **kwargs)
        if business_location:
            # Filter menu items by business location and availability
            self.fields['menu_item'].queryset = MenuItem.objects.filter(
                business_location=business_location,
                is_available=True
            )


class RestaurantOrderForm(forms.ModelForm):
    """Form for creating and editing restaurant orders."""

    class Meta:
        model = RestaurantOrder
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Make delivery_address required only for delivery orders
        self.fields['delivery_address'].required = False
        self.fields['table_number'].required = False

    def clean(self):
        cleaned_data = super().clean()
        order_type = cleaned_data.get('order_type')
        delivery_address = cleaned_data.get('delivery_address')
        table_number = cleaned_data.get('table_number')

        if order_type == 'DELIVERY' and not delivery_address:
            self.add_error('delivery_address', _('Delivery address is required for delivery orders.'))
        elif order_type == 'DINE_IN' and not table_number:
            self.add_error('table_number', _('Table number is required for dine-in orders.'))

        return cleaned_data


class OrderStatusForm(forms.ModelForm):
    """Form for updating order status."""
    
    status = forms.ChoiceField(
        label=_('New Status'),
        choices=RestaurantOrder.STATUS_CHOICES,
        required=True
    )
    notes = forms.CharField(
        label=_('Notes'),
        widget=forms.Textarea(attrs={'rows': 3}),
        required=False
    )

    class Meta:
        model = RestaurantOrder
        fields = ['status', 'notes']

    def __init__(self, *args, instance=None, **kwargs):
        super().__init__(*args, **kwargs)
        if instance:
            # Filter out invalid status transitions
            current_status = instance.status
            valid_transitions = {
                'PENDING': ['CONFIRMED', 'CANCELLED'],
                'CONFIRMED': ['PREPARING', 'CANCELLED'],
                'PREPARING': ['READY', 'CANCELLED'],
                'READY': ['DELIVERED', 'CANCELLED'],
                'DELIVERED': ['COMPLETED'],
                'CANCELLED': [],
                'COMPLETED': [],
            }
            
            choices = [
                (status, label) 
                for status, label in RestaurantOrder.STATUS_CHOICES
                if status in valid_transitions.get(current_status, [])
            ]
            self.fields['status'].choices = choices 


class OrderPaymentForm(forms.ModelForm):
    """Form for updating order payment status."""
    class Meta:
        model = RestaurantOrder
        fields = ['payment_status']


class OrderCancellationForm(forms.ModelForm):
    """Form for cancelling an order."""
    class Meta:
        model = RestaurantOrder
        fields = ['cancellation_reason']
        widgets = {
            'cancellation_reason': forms.Textarea(attrs={'rows': 3}),
        }

    def clean_cancellation_reason(self):
        reason = self.cleaned_data.get('cancellation_reason')
        if not reason:
            raise forms.ValidationError(_('Please provide a reason for cancellation.'))
        return reason 


class CustomRestaurantOrderForm(forms.ModelForm):
    """Formulaire personnalisé pour la création de commande restaurant."""
    class Meta:
        model = RestaurantOrder
        exclude = [
            'customer',
            'special_instructions',
            'customer_notes',
            'restaurant_notes',
            'cancellation_reason',
            'cancelled_at',
            'order_number',  # généré automatiquement
            'created_at',
            'updated_at',
            'subtotal',
            'tax_amount',
            'delivery_fee',
            'total_amount',
            'commission_amount',
        ]

    def __init__(self, *args, business_location=None, **kwargs):
        super().__init__(*args, **kwargs)
        # Fixer les valeurs par défaut et rendre certains champs non modifiables
        self.fields['status'].initial = 'READY'
        self.fields['status'].widget = forms.HiddenInput()
        self.fields['payment_status'].initial = 'PAID'
        self.fields['payment_status'].widget = forms.HiddenInput()
        self.fields['payment_method'].initial = 'CASH'
        self.fields['payment_method'].widget = forms.HiddenInput()
        
        # Rendre les champs requis
        if 'order_type' in self.fields:
            self.fields['order_type'].required = True
            self.fields['order_type'].initial = 'DINE_IN'  # Valeur par défaut
        if 'subtotal' in self.fields:
            self.fields['subtotal'].required = True
            self.fields['subtotal'].widget = forms.HiddenInput()
        
        if business_location:
            self.fields['business_location'].initial = business_location
            self.fields['business_location'].widget.attrs['readonly'] = True
            self.fields['business_location'].disabled = True
        # Optionnel : masquer customer si déjà connu
        # self.fields['customer'].widget = forms.HiddenInput() 


class OrderCustomerForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email', 'phone_number']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Prénom', 'required': True}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom', 'required': True}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email', 'required': True}),
            'phone_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Téléphone', 'required': True}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Rendre tous les champs requis
        self.fields['first_name'].required = True
        self.fields['last_name'].required = True
        self.fields['email'].required = True
        self.fields['phone_number'].required = True 