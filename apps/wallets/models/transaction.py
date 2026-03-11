from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator
from apps.core.models import TimeStampedModel
from .wallet import UserWallet, BusinessWallet
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType


class AbstractTransaction(TimeStampedModel):
    """
    Modèle transaction abstrait : hérité par UserTransaction et BusinessTransaction.
    """
    TRANSACTION_TYPES = (
        ('DEPOSIT',    _('Deposit')),
        ('WITHDRAWAL', _('Withdrawal')),
        ('TRANSFER',   _('Transfer')),
        ('PAYMENT',    _('Payment')),
        ('CASH_PAYMENT', _('Cash Payment')),
        ('HOLD',       _('Hold')),
        ('REFUND',     _('Refund')),
    )
    
    STATUS_CHOICES = (
        ('PENDING',   _('Pending')),
        ('COMPLETED', _('Completed')),
        ('FAILED',    _('Failed')),
        ('CANCELLED', _('Cancelled')),
    )

    transaction_type = models.CharField(
        _('Transaction Type'),
        max_length=20,
        choices=TRANSACTION_TYPES
    )
    amount = models.DecimalField(
        _('Amount'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0.00)]
    )
    status = models.CharField(
        _('Status'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='PENDING'
    )
    reference = models.CharField(
        _('Reference'),
        max_length=100,
        unique=True,
        help_text=_('Unique transaction reference')
    )
    description = models.TextField(
        _('Description'),
        blank=True
    )
    related_transaction = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='related_transactions',
        verbose_name=_('Related Transaction')
    )

    class Meta:
        abstract = True
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['reference']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.amount} ({self.reference})"

    def mark_as_completed(self):
        self.status = 'COMPLETED'
        self.save()

    def mark_as_failed(self):
        self.status = 'FAILED'
        self.save()

    def mark_as_cancelled(self):
        self.status = 'CANCELLED'
        self.save()


class UserTransaction(AbstractTransaction):
    wallet_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, related_name='+', null=True, blank=True)
    wallet_object_id = models.PositiveIntegerField(null=True, blank=True)
    wallet = GenericForeignKey('wallet_content_type', 'wallet_object_id')
    # Lien générique vers n'importe quel objet (ex: réservation)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True, related_name='+')
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey('content_type', 'object_id')

    class Meta(AbstractTransaction.Meta):
        verbose_name = _('User Transaction')
        verbose_name_plural = _('User Transactions')
        indexes = AbstractTransaction.Meta.indexes + [
        ]


# 3. Transaction pour BusinessWallet
class BusinessTransaction(AbstractTransaction):
    wallet = models.ForeignKey(
        BusinessWallet,
        on_delete=models.PROTECT,
        related_name='transactions',
        verbose_name=_('Business Wallet')
    )

    class Meta(AbstractTransaction.Meta):
        verbose_name = _('Business Transaction')
        verbose_name_plural = _('Business Transactions')
        indexes = AbstractTransaction.Meta.indexes + [
            models.Index(fields=['wallet', '-created_at']),
        ]