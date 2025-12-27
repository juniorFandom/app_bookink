from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from apps.business.models import Business
from .models import UserWallet, BusinessWallet, UserTransaction, BusinessTransaction
from .services.transaction_service import TransactionService

User = get_user_model()


class UserWalletForm(forms.ModelForm):
    """Formulaire pour la création/modification d'un wallet utilisateur."""
    
    class Meta:
        model = UserWallet
        fields = ['currency', 'is_active']
        widgets = {
            'currency': forms.Select(choices=[
                ('XAF', 'XAF - Franc CFA'),
                ('USD', 'USD - US Dollar'),
                ('EUR', 'EUR - Euro'),
            ]),
        }


class BusinessWalletForm(forms.ModelForm):
    """Formulaire pour la création/modification d'un wallet entreprise."""
    
    class Meta:
        model = BusinessWallet
        fields = ['currency', 'is_active']
        widgets = {
            'currency': forms.Select(choices=[
                ('XAF', 'XAF - Franc CFA'),
                ('USD', 'USD - US Dollar'),
                ('EUR', 'EUR - Euro'),
            ]),
        }


class UserTransactionForm(forms.ModelForm):
    """Formulaire pour la création d'une transaction utilisateur."""
    
    class Meta:
        model = UserTransaction
        fields = ['transaction_type', 'amount', 'description']
        widgets = {
            'transaction_type': forms.Select(choices=[
                ('DEPOSIT', _('Deposit')),
                ('WITHDRAWAL', _('Withdrawal')),
                ('PAYMENT', _('Payment')),
            ]),
            'amount': forms.NumberInput(attrs={'min': '0.01', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.wallet = kwargs.pop('wallet', None)
        super().__init__(*args, **kwargs)

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        transaction_type = self.cleaned_data.get('transaction_type')
        
        if transaction_type == 'WITHDRAWAL' and self.wallet:
            if not self.wallet.has_sufficient_funds(amount):
                raise forms.ValidationError(_('Insufficient funds in wallet.'))
        
        return amount

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.wallet:
            instance.wallet = self.wallet
            instance.reference = TransactionService.generate_reference()
            instance.status = 'PENDING'
        
        if commit:
            instance.save()
        return instance


class BusinessTransactionForm(forms.ModelForm):
    """Formulaire pour la création d'une transaction entreprise."""
    
    class Meta:
        model = BusinessTransaction
        fields = ['transaction_type', 'amount', 'description']
        widgets = {
            'transaction_type': forms.Select(choices=[
                ('DEPOSIT', _('Deposit')),
                ('WITHDRAWAL', _('Withdrawal')),
                ('PAYMENT', _('Payment')),
            ]),
            'amount': forms.NumberInput(attrs={'min': '0.01', 'step': '0.01'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.wallet = kwargs.pop('wallet', None)
        super().__init__(*args, **kwargs)

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        transaction_type = self.cleaned_data.get('transaction_type')
        
        if transaction_type == 'WITHDRAWAL' and self.wallet:
            if not self.wallet.has_sufficient_funds(amount):
                raise forms.ValidationError(_('Insufficient funds in wallet.'))
        
        return amount

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.wallet:
            instance.wallet = self.wallet
            instance.reference = TransactionService.generate_reference()
            instance.status = 'PENDING'
        
        if commit:
            instance.save()
        return instance


class DepositForm(forms.ModelForm):
    class Meta:
        model = UserTransaction
        fields = ['amount']
        widgets = {
            'amount': forms.NumberInput(attrs={'min': '25', 'step': '25'}),
        }

class WithdrawalForm(forms.Form):
    """Formulaire pour les retraits."""
    
    amount = forms.DecimalField(
        label=_('Amount'),
        min_value=0.01,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'})
    )
    description = forms.CharField(
        label=_('Description'),
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        self.wallet = kwargs.pop('wallet', None)
        super().__init__(*args, **kwargs)

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if self.wallet and not self.wallet.has_sufficient_funds(amount):
            raise forms.ValidationError(_('Insufficient funds in wallet.'))
        return amount


class TransferForm(forms.Form):
    """Formulaire pour les transferts."""
    
    recipient_type = forms.ChoiceField(
        label=_('Recipient Type'),
        choices=[
            ('user', _('User')),
            ('business', _('Business')),
        ],
        widget=forms.RadioSelect
    )
    
    recipient_identifier = forms.CharField(
        label=_('Recipient Identifier'),
        help_text=_('Enter username for user or business name for business'),
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    amount = forms.DecimalField(
        label=_('Amount'),
        min_value=0.01,
        decimal_places=2,
        widget=forms.NumberInput(attrs={'step': '0.01', 'class': 'form-control'})
    )
    
    description = forms.CharField(
        label=_('Description'),
        required=False,
        widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'})
    )

    def __init__(self, *args, **kwargs):
        self.sender_wallet = kwargs.pop('wallet', None)
        super().__init__(*args, **kwargs)

    def clean_amount(self):
        amount = self.cleaned_data['amount']
        if self.sender_wallet and not self.sender_wallet.has_sufficient_funds(amount):
            raise forms.ValidationError(_('Insufficient funds for transfer.'))
        return amount

    def clean_recipient_identifier(self):
        recipient_type = self.cleaned_data.get('recipient_type')
        identifier = self.cleaned_data['recipient_identifier']
        
        if recipient_type == 'user':
            try:
                user = User.objects.get(username=identifier)
                wallet = UserWallet.objects.get(user=user)
            except (User.DoesNotExist, UserWallet.DoesNotExist):
                raise forms.ValidationError(_('User not found or has no wallet.'))
        elif recipient_type == 'business':
            try:
                business = Business.objects.get(name=identifier)
                wallet = BusinessWallet.objects.get(business=business)
            except (Business.DoesNotExist, BusinessWallet.DoesNotExist):
                raise forms.ValidationError(_('Business not found or has no wallet.'))
        else:
            raise forms.ValidationError(_('Invalid recipient type.'))
        
        if self.sender_wallet and wallet.id == self.sender_wallet.id:
            raise forms.ValidationError(_('Cannot transfer to the same wallet.'))
        
        return identifier

    def get_recipient_wallet(self):
        """Récupère le wallet du destinataire."""
        recipient_type = self.cleaned_data.get('recipient_type')
        identifier = self.cleaned_data.get('recipient_identifier')
        
        if recipient_type == 'user':
            user = User.objects.get(username=identifier)
            return UserWallet.objects.get(user=user)
        elif recipient_type == 'business':
            business = Business.objects.get(name=identifier)
            return BusinessWallet.objects.get(business=business)
        
        return None 