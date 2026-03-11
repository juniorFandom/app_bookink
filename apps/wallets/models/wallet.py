from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from apps.core.models import TimeStampedModel
from apps.business.models import Business
from django.contrib.contenttypes.fields import GenericRelation

# 1. Modèle abstrait
class AbstractWallet(TimeStampedModel):
    """
    Wallet de base : ne crée pas de table, hérité par des modèles concrets.
    """
    balance = models.DecimalField(
        _('Balance'),
        max_digits=10,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0.00)]
    )
    is_active = models.BooleanField(_('Active'), default=True)
    currency = models.CharField(
        _('Currency'),
        max_length=3,
        default='XAF',
        help_text=_('Three-letter currency code (e.g. XAF)')
    )

    class Meta:
        abstract = True
        ordering = ['-created_at']

    def __str__(self):
        # Cette méthode sera appelée dans les sous-classes
        return f"{self.owner_repr} ({self.balance} {self.currency})"

    def deposit(self, amount):
        if amount > 0:
            self.balance += amount
            self.save()
            return True
        return False

    def withdraw(self, amount):
        if 0 < amount <= self.balance:
            self.balance -= amount
            self.save()
            return True
        return False

    def has_sufficient_funds(self, amount):
        return self.balance >= amount

    @property
    def owner_repr(self):
        # à redéfinir dans chaque sous-classe pour __str__
        return "Wallet"


# 2. Implémentation pour User
class UserWallet(AbstractWallet):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wallet',
        verbose_name=_('User')
    )
    transactions = GenericRelation(
        'wallets.UserTransaction',
        content_type_field='wallet_content_type',
        object_id_field='wallet_object_id',
        related_query_name='user_wallet'
    )

    class Meta(AbstractWallet.Meta):
        verbose_name = _('User Wallet')
        verbose_name_plural = _('User Wallets')

    @property
    def owner_repr(self):
        return str(self.user)


# 3. Implémentation pour Business
class BusinessWallet(AbstractWallet):
    business = models.OneToOneField(
        Business,
        on_delete=models.CASCADE,
        related_name='wallet',
        verbose_name=_('Business')
    )
    transactions = GenericRelation(
        'wallets.UserTransaction',
        content_type_field='wallet_content_type',
        object_id_field='wallet_object_id',
        related_query_name='business_wallet'
    )

    class Meta(AbstractWallet.Meta):
        verbose_name = _('Business Wallet')
        verbose_name_plural = _('Business Wallets')

    @property
    def owner_repr(self):
        return self.business.name


# 4. Implémentation pour BusinessLocation
class BusinessLocationWallet(AbstractWallet):
    business_location = models.OneToOneField(
        'business.BusinessLocation',
        on_delete=models.CASCADE,
        related_name='wallet',
        verbose_name=_('Business Location')
    )
    transactions = GenericRelation(
        'wallets.UserTransaction',
        content_type_field='wallet_content_type',
        object_id_field='wallet_object_id',
        related_query_name='business_location_wallet'
    )

    class Meta(AbstractWallet.Meta):
        verbose_name = _('Business Location Wallet')
        verbose_name_plural = _('Business Location Wallets')

    @property
    def owner_repr(self):
        return self.business_location.name