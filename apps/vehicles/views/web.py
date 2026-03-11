from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import ListView, DetailView, CreateView, UpdateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.utils import timezone
from ..models import (
    VehicleCategory,
    Vehicle,
    VehicleImage,
    Driver,
    VehicleBooking
)
from ..forms import (
    VehicleCategoryForm,
    VehicleForm,
    VehicleImageForm,
    DriverForm,
    VehicleBookingForm,
    VehicleSearchForm
)
from ..services.vehicle_service import VehicleService, VehicleBookingService
from decimal import Decimal, InvalidOperation
from django.core.exceptions import ValidationError
from apps.wallets.services.wallet_service import WalletService
from apps.wallets.services.transaction_service import TransactionService
from django.db import transaction as db_transaction
from apps.wallets.models.wallet import BusinessLocationWallet
from apps.wallets.models.transaction import UserTransaction
from apps.users.models import User
from django.contrib.contenttypes.models import ContentType
import uuid
from django.views.decorators.http import require_POST

# Create your views here.

class VehicleCategoryListView(ListView):
    model = VehicleCategory
    template_name = 'vehicles/category_list.html'
    context_object_name = 'categories'
    paginate_by = 12

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)

class VehicleCategoryCreateView(LoginRequiredMixin, CreateView):
    model = VehicleCategory
    form_class = VehicleCategoryForm
    template_name = 'vehicles/category_form.html'
    success_url = reverse_lazy('vehicles:category_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Add New Category')
        return context

class VehicleCategoryUpdateView(LoginRequiredMixin, UpdateView):
    model = VehicleCategory
    form_class = VehicleCategoryForm
    template_name = 'vehicles/category_form.html'
    success_url = reverse_lazy('vehicles:category_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Edit Category')
        return context

class VehicleListView(ListView):
    model = Vehicle
    template_name = 'vehicles/vehicle_list.html'
    context_object_name = 'vehicles'
    paginate_by = 12

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(is_available=True)
        return queryset

class VehicleDetailView(DetailView):
    model = Vehicle
    template_name = 'vehicles/vehicle_detail.html'
    context_object_name = 'vehicle'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['search_form'] = VehicleSearchForm()
        return context

class VehicleCreateView(LoginRequiredMixin, CreateView):
    model = Vehicle
    form_class = VehicleForm
    template_name = 'vehicles/vehicle_form.html'
    success_url = reverse_lazy('vehicles:vehicle_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Add New Vehicle')
        return context

class VehicleUpdateView(LoginRequiredMixin, UpdateView):
    model = Vehicle
    form_class = VehicleForm
    template_name = 'vehicles/vehicle_form.html'
    success_url = reverse_lazy('vehicles:vehicle_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Edit Vehicle')
        return context

class VehicleImageCreateView(LoginRequiredMixin, CreateView):
    model = VehicleImage
    form_class = VehicleImageForm
    template_name = 'vehicles/vehicle_image_form.html'
    success_url = reverse_lazy('vehicles:vehicle_list')

    def form_valid(self, form):
        form.instance.vehicle = get_object_or_404(
            Vehicle,
            pk=self.kwargs['vehicle_pk']
        )
        return super().form_valid(form)

class DriverListView(LoginRequiredMixin, ListView):
    model = Driver
    template_name = 'vehicles/driver_list.html'
    context_object_name = 'drivers'
    paginate_by = 10

class DriverDetailView(LoginRequiredMixin, DetailView):
    model = Driver
    template_name = 'vehicles/driver_detail.html'
    context_object_name = 'driver'

class DriverCreateView(LoginRequiredMixin, CreateView):
    model = Driver
    form_class = DriverForm
    template_name = 'vehicles/driver_form.html'
    success_url = reverse_lazy('vehicles:driver_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Add New Driver')
        return context

class DriverUpdateView(LoginRequiredMixin, UpdateView):
    model = Driver
    form_class = DriverForm
    template_name = 'vehicles/driver_form.html'
    success_url = reverse_lazy('vehicles:driver_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Edit Driver')
        return context

class VehicleBookingListView(LoginRequiredMixin, ListView):
    model = VehicleBooking
    template_name = 'vehicles/booking_list.html'
    context_object_name = 'bookings'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(customer=self.request.user)
        return queryset

class VehicleRentalListView(LoginRequiredMixin, ListView):
    model = VehicleBooking
    template_name = 'vehicles/rental_list.html'
    context_object_name = 'bookings'
    paginate_by = 10

    def get_queryset(self):
        queryset = super().get_queryset()
        if not self.request.user.is_staff:
            queryset = queryset.filter(customer=self.request.user)
        return queryset

class VehicleBookingDetailView(LoginRequiredMixin, DetailView):
    model = VehicleBooking
    template_name = 'vehicles/booking_detail.html'
    context_object_name = 'booking'

@login_required
def vehicle_booking_create(request, vehicle_id):
    """Create new vehicle booking avec paiement partiel via wallet utilisateur."""
    vehicle = get_object_or_404(Vehicle, pk=vehicle_id)
    total_amount = None
    pickup_datetime = None
    return_datetime = None
    
    if request.method == 'POST':
        form = VehicleBookingForm(request.POST, vehicle=vehicle)
        # Définir le vehicle et customer sur l'instance avant is_valid()
        form.instance.vehicle = vehicle
        form.instance.customer = request.user
        
        payment_percentage = request.POST.get('payment_percentage')
        try:
            payment_percentage = int(payment_percentage)
            if payment_percentage not in [20, 50, 100]:
                raise ValueError
        except Exception:
            messages.error(request, _("Pourcentage de paiement invalide."))
            return redirect(request.path)
        
        if form.is_valid():
            pickup_datetime = form.cleaned_data['pickup_datetime']
            return_datetime = form.cleaned_data['return_datetime']
            
            # Calculer la durée en jours
            delta = return_datetime - pickup_datetime
            days = delta.days + 1
            
            if days <= 0:
                messages.error(request, _("La durée de location doit être d'au moins 1 jour."))
                return redirect(request.path)
            
            # Calculer le montant total
            daily_rate = form.cleaned_data['daily_rate']
            # Calculer les frais de chauffeur basés sur with_driver
            driver_fee = 0
            if form.cleaned_data['with_driver']:
                # Utiliser le taux journalier du chauffeur du véhicule
                driver_fee = getattr(vehicle, 'driver_daily_rate', 0) * days
            additional_charges = form.cleaned_data['additional_charges']
            
            subtotal = daily_rate * days
            total_amount = subtotal + driver_fee + additional_charges
            amount_to_pay = (Decimal(payment_percentage) / 100) * total_amount
            
            # Vérification du wallet utilisateur
            wallet = WalletService.get_user_wallet(request.user)
            if not wallet or not wallet.is_active:
                messages.error(request, _("Votre wallet utilisateur n'est pas actif. Veuillez contacter le support."))
                return redirect(request.path)
            
            if not WalletService.check_sufficient_funds(wallet, amount_to_pay):
                messages.error(request, _(f"Votre solde est insuffisant pour payer {amount_to_pay:.0f} XAF. Veuillez recharger votre wallet."))
                return redirect(request.path)
            
            # Débit du wallet et création de la transaction HOLD
            try:
                with db_transaction.atomic():
                    # Débiter le wallet
                    WalletService.update_wallet_balance(wallet, amount_to_pay, 'subtract')
                    
                    # Calculate commission
                    business_location = vehicle.business_location
                    commission_amount = business_location.business.calculate_commission(amount_to_pay)
                    
                    # Calculate net amount for business (amount_paid - commission)
                    net_amount = amount_to_pay - commission_amount
                    
                    # Get business location wallet
                    business_wallet = BusinessLocationWallet.objects.select_for_update().get(business_location=business_location)
                    
                    # Get super admin wallet
                    super_admin = User.objects.filter(is_superuser=True).first()
                    if not super_admin:
                        super_admin = User.objects.order_by('id').first()
                    
                    super_admin_wallet = getattr(super_admin, 'wallet', None)
                    
                    # Credit business location with net amount
                    if not business_wallet.deposit(net_amount):
                        raise ValidationError(f"Erreur lors du crédit du wallet business pour {business_location.name}.")
                    
                    # Créer la réservation (statut PENDING)
                    booking = form.save(commit=False)
                    booking.customer = request.user
                    booking.vehicle = vehicle
                    booking.status = 'PENDING'
                    booking.total_days = days
                    booking.subtotal = subtotal
                    booking.total_amount = total_amount
                    booking.amount_paid = amount_to_pay
                    booking.commission_amount = commission_amount
                    
                    # Sauvegarder la réservation AVANT de créer les transactions
                    booking.save()
                    
                    # Create transaction for business location
                    UserTransaction.objects.create(
                        wallet=business_wallet,
                        transaction_type='PAYMENT',
                        amount=net_amount,
                        status='COMPLETED',
                        reference=str(uuid.uuid4()),
                        description=f"Paiement partiel véhicule {vehicle.make} {vehicle.model} (après commission)",
                        content_type=ContentType.objects.get_for_model(booking),
                        object_id=booking.pk,
                        created_at=timezone.now()
                    )
                    
                    # Credit super admin with commission
                    if commission_amount > 0 and super_admin_wallet:
                        if not super_admin_wallet.deposit(commission_amount):
                            raise ValidationError("Erreur lors du crédit de la commission au wallet admin.")
                        
                        # Create commission transaction
                        UserTransaction.objects.create(
                            wallet=super_admin_wallet,
                            transaction_type='COMMISSION',
                            amount=commission_amount,
                            status='COMPLETED',
                            reference=str(uuid.uuid4()),
                            description=f"Commission réservation véhicule {vehicle.make} {vehicle.model}",
                            content_type=ContentType.objects.get_for_model(booking),
                            object_id=booking.pk,
                            created_at=timezone.now()
                        )
                    
                    # Créer la transaction HOLD pour l'utilisateur
                    description = f"Réservation véhicule {vehicle.make} {vehicle.model} ({payment_percentage}% du montant total)"
                    user_transaction = UserTransaction.objects.create(
                        wallet=wallet,
                        transaction_type='HOLD',
                        amount=amount_to_pay,
                        status='COMPLETED',
                        reference=str(uuid.uuid4()),
                        description=description,
                        content_type=ContentType.objects.get_for_model(booking),
                        object_id=booking.pk,
                        created_at=timezone.now()
                    )
                    
                    messages.success(request, _(f"Réservation créée avec succès ! {amount_to_pay:.0f} XAF ont été débités de votre wallet."))
                    return redirect('vehicles:booking_detail', pk=booking.pk)
            except Exception as e:
                messages.error(request, _(f"Erreur lors du paiement ou de la réservation : {str(e)}"))
                return redirect(request.path)
        else:
            pickup_datetime = form.data.get('pickup_datetime')
            return_datetime = form.data.get('return_datetime')
    else:
        form = VehicleBookingForm(vehicle=vehicle)
        # Définir le vehicle et customer sur l'instance
        form.instance.vehicle = vehicle
        form.instance.customer = request.user
        # Initialiser le champ customer dans le formulaire
        form.fields['customer'].initial = request.user.pk
        pickup_datetime = request.GET.get('pickup_datetime')
        return_datetime = request.GET.get('return_datetime')
    
    # Calcul du montant total si les dates sont présentes
    from datetime import datetime
    try:
        if pickup_datetime and return_datetime:
            # Convertir les chaînes en objets datetime
            if isinstance(pickup_datetime, str):
                pickup_dt = datetime.fromisoformat(pickup_datetime.replace('Z', '+00:00'))
            else:
                pickup_dt = pickup_datetime
                
            if isinstance(return_datetime, str):
                return_dt = datetime.fromisoformat(return_datetime.replace('Z', '+00:00'))
            else:
                return_dt = return_datetime
                
            delta = return_dt - pickup_dt
            days = delta.days + 1
            if days > 0:
                total_amount = vehicle.daily_rate * days
    except Exception:
        total_amount = None
    
    context = {
        'form': form,
        'vehicle': vehicle,
        'pickup_datetime': pickup_datetime,
        'return_datetime': return_datetime,
        'duration_days': days if pickup_datetime and return_datetime and 'days' in locals() else '',
        'total_amount': total_amount,
    }
    return render(request, 'vehicles/booking_form.html', context)

class VehicleBookingUpdateView(LoginRequiredMixin, UpdateView):
    model = VehicleBooking
    form_class = VehicleBookingForm
    template_name = 'vehicles/booking_form.html'
    success_url = reverse_lazy('vehicles:booking_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _('Edit Booking')
        return context

def vehicle_search_view(request):
    """View for searching available vehicles."""
    form = VehicleSearchForm(request.GET)
    vehicles = []

    if form.is_valid():
        vehicles = VehicleService.search_available_vehicles(
            start_date=form.cleaned_data['pickup_datetime'],
            end_date=form.cleaned_data['return_datetime'],
            category=form.cleaned_data['category'],
            passenger_capacity=form.cleaned_data['passenger_capacity'],
            transmission=form.cleaned_data['transmission'],
            max_daily_rate=form.cleaned_data['max_daily_rate']
        )

    return render(request, 'vehicles/vehicle_search_results.html', {
        'form': form,
        'vehicles': vehicles
    })

def vehicle_booking_payment_view(request, pk):
    """View for handling rental payments."""
    booking = get_object_or_404(VehicleBooking, pk=pk)
    
    if request.method == 'POST':
        amount_str = request.POST.get('amount')
        if amount_str:
            try:
                amount = Decimal(amount_str)
                VehicleBookingService.process_payment(booking, amount)
                messages.success(request, _('Payment processed successfully'))
                return redirect('vehicles:booking_detail', pk=booking.pk)
            except (ValueError, InvalidOperation):
                messages.error(request, _('Invalid amount'))
            except ValidationError as e:
                messages.error(request, e.message)
    
    return render(request, 'vehicles/booking_payment.html', {
        'booking': booking
    })

@login_required
def finalize_payment_admin(request, pk):
    """Affiche la page de finalisation du paiement en espèces avec modale de confirmation."""
    booking = get_object_or_404(VehicleBooking, pk=pk)
    
    # Vérifier que l'utilisateur est le propriétaire du business
    if booking.vehicle.business_location.business.owner != request.user:
        messages.error(request, "Vous n'avez pas l'autorisation de finaliser cette transaction.")
        return redirect('vehicles:booking_list')
    
    # Vérifier que la réservation est en attente
    if booking.status != 'PENDING':
        messages.error(request, "Cette réservation n'est pas en attente de paiement.")
        return redirect('vehicles:booking_list')
    
    # Récupérer la transaction HOLD originale
    hold_transaction = booking.transactions.filter(transaction_type='HOLD', status='COMPLETED').first()
    if not hold_transaction:
        messages.error(request, "Aucune transaction HOLD trouvée pour cette réservation.")
        return redirect('vehicles:booking_list')
    
    hold_amount = hold_transaction.amount
    total_amount = booking.total_amount
    remaining_amount = total_amount - hold_amount

    if remaining_amount <= 0:
        messages.info(request, "Aucun montant restant à payer.")
        return redirect('vehicles:booking_list')

    context = {
        'booking': booking,
        'hold_amount': hold_amount,
        'remaining_amount': remaining_amount,
        'total_amount': total_amount,
    }
    return render(request, 'vehicles/finalize_payment_admin.html', context)


@login_required
@require_POST
def process_cash_payment(request, pk):
    """Traite le paiement en espèces et approuve la réservation avec nouvelle logique de transactions."""
    booking = get_object_or_404(VehicleBooking, pk=pk)
    
    # Vérifier que l'utilisateur est le propriétaire du business
    if booking.vehicle.business_location.business.owner != request.user:
        messages.error(request, "Vous n'avez pas l'autorisation de finaliser cette transaction.")
        return redirect('vehicles:booking_list')
    
    # Vérifier que la réservation est en attente
    if booking.status != 'PENDING':
        messages.error(request, "Cette réservation n'est pas en attente de paiement.")
        return redirect('vehicles:booking_list')
    
    # Récupérer la transaction HOLD originale
    hold_transaction = booking.transactions.filter(transaction_type='HOLD', status='COMPLETED').first()
    if not hold_transaction:
        messages.error(request, "Aucune transaction HOLD trouvée pour cette réservation.")
        return redirect('vehicles:booking_list')
    
    hold_amount = hold_transaction.amount
    total_amount = booking.total_amount
    remaining_amount = total_amount - hold_amount

    try:
        with db_transaction.atomic():
            # 1. Rembourser le montant HOLD au wallet utilisateur
            customer_wallet = WalletService.get_user_wallet(booking.customer)
            if customer_wallet and customer_wallet.is_active:
                customer_wallet.deposit(hold_amount)
                
                # Créer une transaction de remboursement pour le HOLD
                refund_transaction = UserTransaction.objects.create(
                    wallet=customer_wallet,
                    transaction_type='REFUND',
                    amount=hold_amount,
                    description=f"Remboursement transaction HOLD - Réservation véhicule {booking.vehicle.make} {booking.vehicle.model}",
                    status='COMPLETED',
                    reference=f"REFUND-HOLD-{booking.booking_reference}-{uuid.uuid4().hex[:8]}",
                    content_type=ContentType.objects.get_for_model(booking),
                    object_id=booking.pk,
                    created_at=timezone.now()
                )
                booking.transactions.add(refund_transaction)
            
            # 2. Créer une nouvelle transaction PAYMENT avec le montant HOLD
            payment_transaction = UserTransaction.objects.create(
                wallet=customer_wallet,
                transaction_type='PAYMENT',
                amount=hold_amount,
                description=f"Paiement finalisé - Réservation véhicule {booking.vehicle.make} {booking.vehicle.model} (montant HOLD)",
                status='COMPLETED',
                reference=f"PAY-HOLD-{booking.booking_reference}-{uuid.uuid4().hex[:8]}",
                content_type=ContentType.objects.get_for_model(booking),
                object_id=booking.pk,
                created_at=timezone.now()
            )
            booking.transactions.add(payment_transaction)
            
            # 3. Créer une transaction CASH_PAYMENT pour le reste du montant
            if remaining_amount > 0:
                cash_payment_transaction = UserTransaction.objects.create(
                    wallet=customer_wallet,
                    transaction_type='CASH_PAYMENT',
                    amount=remaining_amount,
                    description=f"Paiement en espèces - Réservation véhicule {booking.vehicle.make} {booking.vehicle.model} (reste)",
                    status='COMPLETED',
                    reference=f"PAY-CASH-{booking.booking_reference}-{uuid.uuid4().hex[:8]}",
                    content_type=ContentType.objects.get_for_model(booking),
                    object_id=booking.pk,
                    created_at=timezone.now()
                )
                booking.transactions.add(cash_payment_transaction)
            
            # 4. Calculate commission and update business location wallet
            business_location = booking.vehicle.business_location
            commission_amount = business_location.business.calculate_commission(total_amount)
            booking.commission_amount = commission_amount
            
            # Calculate net amount for business (total - commission)
            net_amount = total_amount - commission_amount
            
            business_location_wallet = getattr(business_location, 'wallet', None)
            if business_location_wallet:
                # Credit business location with net amount
                business_location_wallet.deposit(net_amount)
                
                # Create transaction for business location
                business_transaction = UserTransaction.objects.create(
                    wallet=business_location_wallet,
                    transaction_type='PAYMENT',
                    amount=net_amount,
                    description=f"Paiement net reçu - Réservation véhicule {booking.vehicle.make} {booking.vehicle.model} (après commission)",
                    status='COMPLETED',
                    reference=f"PAY-BUSINESS-{booking.booking_reference}-{uuid.uuid4().hex[:8]}",
                    content_type=ContentType.objects.get_for_model(booking),
                    object_id=booking.pk,
                    created_at=timezone.now()
                )
                booking.transactions.add(business_transaction)
            
            # 5. Credit super admin with commission
            super_admin = User.objects.filter(is_superuser=True).first()
            if not super_admin:
                super_admin = User.objects.order_by('id').first()
            
            super_admin_wallet = getattr(super_admin, 'wallet', None)
            
            if commission_amount > 0 and super_admin_wallet:
                super_admin_wallet.deposit(commission_amount)
                
                # Create commission transaction
                UserTransaction.objects.create(
                    wallet=super_admin_wallet,
                    transaction_type='COMMISSION',
                    amount=commission_amount,
                    status='COMPLETED',
                    reference=f"COM-VEHICLE-{booking.booking_reference}-{uuid.uuid4().hex[:8]}",
                    description=f"Commission réservation véhicule {booking.vehicle.make} {booking.vehicle.model} - {business_location.name}",
                    content_type=ContentType.objects.get_for_model(booking),
                    object_id=booking.pk,
                    created_at=timezone.now()
                )
            
            # 6. Marquer la transaction HOLD comme CANCELLED
            hold_transaction.status = 'CANCELLED'
            hold_transaction.save()
            
            # 7. Mettre à jour le statut de la réservation
            booking.status = 'CONFIRMED'
            booking.save()
            
            messages.success(request, f"Paiement finalisé avec succès ! Montant HOLD: {hold_amount:.0f} XAF, Reste en espèces: {remaining_amount:.0f} XAF. Total: {total_amount:.0f} XAF.")
            
    except Exception as e:
        messages.error(request, f"Erreur lors de la finalisation : {str(e)}")

    return redirect('vehicles:booking_list')


@login_required
@require_POST
def approve_booking(request, pk):
    """Approuve une réservation en utilisant la nouvelle logique de transactions."""
    booking = get_object_or_404(VehicleBooking, pk=pk)
    
    # Vérifier que l'utilisateur est le propriétaire du business
    if booking.vehicle.business_location.business.owner != request.user:
        messages.error(request, "Vous n'avez pas l'autorisation d'approuver cette réservation.")
        return redirect('vehicles:booking_list')
    
    # Vérifier que la réservation est en attente
    if booking.status != 'PENDING':
        messages.error(request, "Cette réservation n'est pas en attente d'approbation.")
        return redirect('vehicles:booking_list')
    
    # Récupérer la transaction HOLD originale
    hold_transaction = booking.transactions.filter(transaction_type='HOLD', status='COMPLETED').first()
    if not hold_transaction:
        messages.error(request, "Aucune transaction HOLD trouvée pour cette réservation.")
        return redirect('vehicles:booking_list')
    
    hold_amount = hold_transaction.amount
    total_amount = booking.total_amount
    
    # Si le montant HOLD ne couvre pas le total, rediriger vers la finalisation du paiement
    if hold_amount < total_amount:
        return redirect('vehicles:finalize_payment_admin', pk=pk)
    
    # Sinon, approuver directement la réservation avec la nouvelle logique
    try:
        with db_transaction.atomic():
            # 1. Rembourser le montant HOLD au wallet utilisateur
            customer_wallet = WalletService.get_user_wallet(booking.customer)
            if customer_wallet and customer_wallet.is_active:
                customer_wallet.deposit(hold_amount)
                
                # Créer une transaction de remboursement pour le HOLD
                refund_transaction = UserTransaction.objects.create(
                    wallet=customer_wallet,
                    transaction_type='REFUND',
                    amount=hold_amount,
                    description=f"Remboursement transaction HOLD - Réservation véhicule {booking.vehicle.make} {booking.vehicle.model}",
                    status='COMPLETED',
                    reference=f"REFUND-HOLD-{booking.booking_reference}-{uuid.uuid4().hex[:8]}",
                    content_type=ContentType.objects.get_for_model(booking),
                    object_id=booking.pk,
                    created_at=timezone.now()
                )
                booking.transactions.add(refund_transaction)
            
            # 2. Créer une nouvelle transaction PAYMENT avec le montant HOLD
            payment_transaction = UserTransaction.objects.create(
                wallet=customer_wallet,
                transaction_type='PAYMENT',
                amount=hold_amount,
                description=f"Paiement finalisé - Réservation véhicule {booking.vehicle.make} {booking.vehicle.model} (montant HOLD)",
                status='COMPLETED',
                reference=f"PAY-HOLD-{booking.booking_reference}-{uuid.uuid4().hex[:8]}",
                content_type=ContentType.objects.get_for_model(booking),
                object_id=booking.pk,
                created_at=timezone.now()
            )
            booking.transactions.add(payment_transaction)
            
            # 3. Mettre à jour le wallet de l'établissement
            business_location_wallet = getattr(booking.vehicle.business_location, 'wallet', None)
            if business_location_wallet:
                # Ajouter le montant total au wallet de l'établissement
                business_location_wallet.deposit(total_amount)
                
                # Créer la transaction pour l'établissement
                business_transaction = UserTransaction.objects.create(
                    wallet=business_location_wallet,
                    transaction_type='PAYMENT',
                    amount=total_amount,
                    description=f"Paiement total reçu - Réservation véhicule {booking.vehicle.make} {booking.vehicle.model} - Client: {booking.customer.get_full_name()} (Total: {total_amount:.0f} XAF)",
                    status='COMPLETED',
                    reference=f"PAY-BUSINESS-{booking.booking_reference}-{uuid.uuid4().hex[:8]}",
                    content_type=ContentType.objects.get_for_model(booking),
                    object_id=booking.pk,
                    created_at=timezone.now()
                )
                booking.transactions.add(business_transaction)
                    
            # 4. Marquer la transaction HOLD comme CANCELLED
            hold_transaction.status = 'CANCELLED'
            hold_transaction.save()
            
            # 5. Mettre à jour le statut de la réservation
            booking.status = 'CONFIRMED'
            booking.save()
            
            messages.success(request, f"Réservation {booking.booking_reference} approuvée avec succès. Montant HOLD: {hold_amount:.0f} XAF, Total: {total_amount:.0f} XAF.")
                
    except Exception as e:
        messages.error(request, f"Erreur lors de l'approbation : {str(e)}")
    
    return redirect('vehicles:booking_list')
