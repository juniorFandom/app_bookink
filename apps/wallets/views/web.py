from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
from django.views.generic import DetailView, ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.http import Http404
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

from ..models import UserWallet, BusinessWallet, UserTransaction, BusinessTransaction
from ..forms import DepositForm, WithdrawalForm, TransferForm
from ..services.wallet_service import WalletService
from ..services.transaction_service import TransactionService

User = get_user_model()


# VUES FONCTIONNELLES POUR LES WALLETS

@login_required
def wallet_detail_view(request):
    user = request.user
    wallet, created = WalletService.get_or_create_user_wallet(user)
    recent_transactions = TransactionService.get_wallet_transactions(wallet, limit=10)
    wallet_stats = WalletService.get_wallet_statistics(wallet)
    transaction_stats = TransactionService.get_transaction_statistics(wallet)
    context = {
        'wallet': wallet,
        'recent_transactions': recent_transactions,
        'wallet_stats': wallet_stats,
        'transaction_stats': transaction_stats,
    }
    return render(request, 'wallets/wallet_detail.html', context)

@login_required
def transaction_list_view(request):
    user = request.user
    wallet = WalletService.get_user_wallet(user)
    if not wallet:
        transactions = UserTransaction.objects.none()
    else:
        transactions = wallet.transactions.all()
    paginator = Paginator(transactions, 20)
    page = request.GET.get('page')
    try:
        transactions_page = paginator.page(page)
    except PageNotAnInteger:
        transactions_page = paginator.page(1)
    except EmptyPage:
        transactions_page = paginator.page(paginator.num_pages)
    context = {
        'transactions': transactions_page,
        'wallet': wallet,
        'wallet_stats': WalletService.get_wallet_statistics(wallet) if wallet else None,
    }
    return render(request, 'wallets/transaction_list.html', context)

@login_required
def transaction_detail_view(request, pk):
    user = request.user
    wallet = WalletService.get_user_wallet(user)
    if not wallet:
        raise Http404("Wallet not found")
    transaction = get_object_or_404(UserTransaction, id=pk, wallet=wallet)
    context = {'transaction': transaction}
    return render(request, 'wallets/transaction_detail.html', context)

@login_required
def deposit_view(request):
    user = request.user
    wallet = WalletService.get_user_wallet(user)
    if request.method == 'POST':
        form = DepositForm(request.POST, instance=UserTransaction(wallet=wallet))
        if form.is_valid():
            try:
                transaction = TransactionService.process_deposit(
                    wallet=wallet,
                    amount=form.cleaned_data['amount'],
                    description=form.cleaned_data.get('description', '')
                )
                messages.success(
                    request,
                    _('Deposit of {amount} {currency} completed successfully. Reference: {reference}').format(
                        amount=transaction.amount,
                        currency=wallet.currency,
                        reference=transaction.reference
                    )
                )
                return redirect('wallets:wallet_detail')
            except Exception as e:
                messages.error(request, str(e))
    else:
        form = DepositForm(instance=UserTransaction(wallet=wallet))
    context = {'form': form, 'wallet': wallet}
    return render(request, 'wallets/deposit.html', context)

@login_required
def withdrawal_view(request):
    user = request.user
    wallet = WalletService.get_user_wallet(user)
    if request.method == 'POST':
        form = WithdrawalForm(request.POST)
        form.wallet = wallet
        if form.is_valid():
            try:
                transaction = TransactionService.process_withdrawal(
                    wallet=wallet,
                    amount=form.cleaned_data['amount'],
                    description=form.cleaned_data.get('description', '')
                )
                messages.success(
                    request,
                    _('Withdrawal of {amount} {currency} completed successfully. Reference: {reference}').format(
                        amount=transaction.amount,
                        currency=wallet.currency,
                        reference=transaction.reference
                    )
                )
                return redirect('wallets:wallet_detail')
            except Exception as e:
                messages.error(request, str(e))
    else:
        form = WithdrawalForm()
        form.wallet = wallet
    context = {'form': form, 'wallet': wallet}
    return render(request, 'wallets/withdrawal.html', context)

@login_required
def transfer_view(request):
    user = request.user
    wallet = WalletService.get_user_wallet(user)
    if request.method == 'POST':
        form = TransferForm(request.POST)
        form.wallet = wallet
        if form.is_valid():
            try:
                recipient_wallet = form.get_recipient_wallet()
                outgoing_transaction, incoming_transaction = TransactionService.process_transfer(
                    sender_wallet=wallet,
                    recipient_wallet=recipient_wallet,
                    amount=form.cleaned_data['amount'],
                    description=form.cleaned_data.get('description', '')
                )
                messages.success(
                    request,
                    _('Transfer of {amount} {currency} to {recipient} completed successfully. Reference: {reference}').format(
                        amount=outgoing_transaction.amount,
                        currency=wallet.currency,
                        recipient=recipient_wallet.owner_repr,
                        reference=outgoing_transaction.reference
                    )
                )
                return redirect('wallets:wallet_detail')
            except Exception as e:
                messages.error(request, str(e))
    else:
        form = TransferForm()
        form.wallet = wallet
    context = {'form': form, 'wallet': wallet}
    return render(request, 'wallets/transfer.html', context)

@login_required
def business_wallet_detail_view(request):
    user = request.user
    try:
        business = user.business
        wallet, created = WalletService.get_or_create_business_wallet(business)
    except Exception:
        raise Http404("No business found for this user")
    recent_transactions = TransactionService.get_wallet_transactions(wallet, limit=10)
    wallet_stats = WalletService.get_wallet_statistics(wallet)
    transaction_stats = TransactionService.get_transaction_statistics(wallet)
    context = {
        'wallet': wallet,
        'recent_transactions': recent_transactions,
        'wallet_stats': wallet_stats,
        'transaction_stats': transaction_stats,
    }
    return render(request, 'wallets/business_wallet_detail.html', context)
