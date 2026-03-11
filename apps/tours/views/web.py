from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Q
from django.utils import timezone
from django.core.exceptions import ValidationError
from ..models import (
    Tour, TourDestination, TourDestinationImage, TourBooking, TourSchedule, TourReview
)
from apps.business.models import BusinessLocation
from ..forms import (
    TourBookingForm, TourScheduleForm, TourSearchForm
)
from apps.wallets.services.wallet_service import WalletService
from apps.wallets.services.transaction_service import TransactionService
from apps.wallets.models import UserWallet, UserTransaction
from apps.wallets.models.wallet import BusinessLocationWallet
from decimal import Decimal
from django.db import transaction as db_transaction
from django.views.decorators.http import require_POST
from django.http import HttpResponse
from django.contrib.contenttypes.models import ContentType
from ..services.tour_service import TourService
from apps.tours.forms import TourForm
from django.http import JsonResponse
from apps.tourist_sites.models import ZoneDangereuse, ZoneDangereuseVote

def tour_list(request):
    """View for listing all available tours."""
    form = TourSearchForm(request.GET)
    tours = Tour.objects.filter(is_active=True)
    
    if form.is_valid():
        query = form.cleaned_data.get('query')
        tour_type = form.cleaned_data.get('tour_type')
        min_price = form.cleaned_data.get('min_price')
        max_price = form.cleaned_data.get('max_price')
        min_duration = form.cleaned_data.get('min_duration')
        max_duration = form.cleaned_data.get('max_duration')
        min_rating = form.cleaned_data.get('min_rating')
        sort_by = form.cleaned_data.get('sort_by')
        verified_only = form.cleaned_data.get('verified_only')
        
        if query:
            tours = tours.filter(
                Q(nom_balade__icontains=query) |
                Q(description__icontains=query)
            )
        
        if tour_type:
            tours = tours.filter(tour_type=tour_type)
            
        if min_price:
            tours = tours.filter(price_per_person__gte=min_price)
            
        if max_price:
            tours = tours.filter(price_per_person__lte=max_price)
            
        if min_duration:
            tours = tours.filter(duration_days__gte=min_duration)
            
        if max_duration:
            tours = tours.filter(duration_days__lte=max_duration)
            
        if min_rating:
            tours = tours.annotate(
                avg_rating=Avg('tour_reviews__rating')
            ).filter(avg_rating__gte=min_rating)
            
        if verified_only:
            tours = tours.filter(business_location__is_verified=True)
            
        if sort_by:
            if sort_by == 'name':
                tours = tours.order_by('nom_balade')
            elif sort_by == 'price':
                tours = tours.order_by('price_per_person')
            elif sort_by == 'duration':
                tours = tours.order_by('duration_days')
            elif sort_by == 'rating':
                tours = tours.annotate(
                    avg_rating=Avg('tour_reviews__rating')
                ).order_by('-avg_rating')
    
    paginator = Paginator(tours, 12)
    page = request.GET.get('page')
    tours = paginator.get_page(page)
    
    return render(request, 'tours/tour_list.html', {
        'tours': tours,
        'form': form
    })

def tour_detail(request, slug):
    """View for displaying tour details."""
    tour = get_object_or_404(Tour, slug=slug, is_active=True)
    destinations = tour.destinations.filter(is_active=True).order_by('day_number')
    reviews = tour.tour_reviews.filter(is_approved=True).order_by('-created_at')
    
    # Get tour statistics
    statistics = TourService.get_tour_statistics(tour)
    # cette requette permet de selectionner tous les hopitaux enregistre dans notre base de donnees tout en capturant les excepions 
    # Get available dates
    available_dates = TourSchedule.objects.filter(
        tour=tour,
        status='SCHEDULED',
        start_datetime__gt=timezone.now()
    ).order_by('start_datetime')
    
    return render(request, 'tours/tour_detail.html', {
        'tour': tour,
        'destinations': destinations,
        'reviews': reviews,
        'statistics': statistics,
        'available_dates': available_dates
    })

@login_required
def tour_create(request):
    """View for creating a new tour."""
    location_id = request.GET.get('location')
    if not location_id:
        messages.error(request, _('Location parameter is required.'))
        return redirect('business:business_list')
    
    location = get_object_or_404(BusinessLocation, pk=location_id)
    
    # Vérifier les permissions
    if request.user != location.business.owner:
        messages.error(request, _('You do not have permission to create tours for this business.'))
        return redirect('business:business_location_dashboard', pk=location.pk)
    
    if request.method == 'POST':
        form = TourForm(request.POST, request.FILES)
        print(f"Form is valid: {form.is_valid()}")
        if not form.is_valid():
            print(f"Form errors: {form.errors}")
            print(f"Form non-field errors: {form.non_field_errors()}")
        if form.is_valid():
            try:
                tour = form.save(commit=False)
                tour.business_location = location
                print(f"About to save tour: {tour.nom_balade}, location: {tour.business_location}")
                tour.save()
                print(f"Tour saved successfully with ID: {tour.pk}")
                messages.success(request, _('Tour created successfully.'))
                return redirect('business:business_location_dashboard', pk=location.pk)
            except Exception as e:
                print(f"Error saving tour: {e}")
                messages.error(request, _(f'Error creating tour: {str(e)}'))
        else:
            messages.error(request, _('Please correct the errors below.'))
    else:
        form = TourForm(initial={'business_location': location})
    
    # Récupérer les destinations disponibles du business
    available_destinations = TourDestination.objects.filter(
        tour__business_location=location,
        is_active=True
    ).distinct()
    
    return render(request, 'tours/tour_form.html', {
        'form': form,
        'location': location,
        'available_destinations': available_destinations,
        'title': _('Create Tour')
    })

@login_required
def tour_edit(request, slug):
    """View for editing an existing tour."""
    tour = get_object_or_404(Tour, slug=slug)
    
    if request.user != tour.business_location.business.owner:
        messages.error(request, _('You do not have permission to edit this tour.'))
        return redirect('tours:tour_detail', slug=tour.slug)
    
    if request.method == 'POST':
        form = TourForm(request.POST, request.FILES, instance=tour)
        if form.is_valid():
            tour = form.save()
            messages.success(request, _('Tour updated successfully.'))
            return redirect('business:business_location_dashboard', pk=tour.business_location.pk)
    else:
        form = TourForm(instance=tour)
    
    # Récupérer les destinations disponibles du business
    available_destinations = TourDestination.objects.filter(
        tour__business_location=tour.business_location,
        is_active=True
    ).distinct()
    
    return render(request, 'tours/tour_form.html', {
        'form': form,
        'tour': tour,
        'location': tour.business_location,
        'available_destinations': available_destinations,
        'title': _('Edit Tour')
    })

@login_required
def tour_image_upload(request, slug):
    """View for uploading tour images."""
    tour = get_object_or_404(Tour, slug=slug)
    
    if request.user != tour.business_location.business.owner:
        messages.error(request, _('You do not have permission to upload images for this tour.'))
        return redirect('tours:tour_detail', slug=tour.slug)
    
    if request.method == 'POST':
        form = TourImageForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.save(commit=False)
            image.tour = tour
            image.save()
            messages.success(request, _('Image uploaded successfully.'))
            return redirect('tours:tour_detail', slug=tour.slug)
    else:
        form = TourImageForm()
    
    return render(request, 'tours/tour_image_form.html', {
        'form': form,
        'tour': tour
    })

@login_required
def tour_booking_create(request, slug):
    """View for creating a tour booking."""
    tour = get_object_or_404(Tour, slug=slug, is_active=True)
    
    if request.method == 'POST':
        form = TourBookingForm(request.POST, tour=tour)
        if form.is_valid():
            try:
                with db_transaction.atomic():
                    # Récupérer les données du formulaire
                    num_participants = form.cleaned_data['number_of_participants']
                    first_name = form.cleaned_data['first_name']
                    email = form.cleaned_data['email']
                    special_requirements = form.cleaned_data.get('special_requirements', '')
                    guide_notes = form.cleaned_data.get('guide_notes', '')
                    payment_percentage = int(form.cleaned_data['payment_percentage'])
                    
                    # Calculer le montant total et le montant à payer
                    total_amount = tour.price_per_person * num_participants
                    amount_to_pay = (total_amount * payment_percentage) / 100
                    
                    # Créer la réservation
                    booking = TourBooking.objects.create(
                        customer=request.user,
                        tour=tour,  # Assigner le tour
                        tour_schedule=None,  # Pour l'instant, pas de schedule spécifique
                        number_of_participants=num_participants,
                        total_amount=total_amount,
                        amount_paid=amount_to_pay,
                        payment_percentage=payment_percentage,
                        special_requests=special_requirements,
                        guide_notes=guide_notes,
                        status='PENDING'
                    )
                    
                    # Créer ou récupérer le wallet de l'utilisateur
                    user_wallet, created = UserWallet.objects.get_or_create(
                        user=request.user,
                        defaults={'balance': 100000.00, 'currency': 'XAF'}  # Solde initial pour la démo
                    )
                    
                    # Vérifier si l'utilisateur a suffisamment de fonds
                    if not user_wallet.has_sufficient_funds(amount_to_pay):
                        messages.error(request, _("Solde insuffisant pour effectuer cette réservation. Veuillez recharger votre wallet."))
                        return redirect(request.path)
                    
                    # Créer la transaction de paiement
                    transaction_description = f"Paiement réservation tour '{tour.nom_balade}' - {num_participants} participant(s) - {payment_percentage}%"
                    
                    user_transaction = UserTransaction.objects.create(
                        wallet=user_wallet,
                        transaction_type='PAYMENT',
                        amount=amount_to_pay,
                        status='COMPLETED',
                        reference=TransactionService.generate_reference(),
                        description=transaction_description,
                        content_type=ContentType.objects.get_for_model(TourBooking),
                        object_id=booking.pk
                    )
                    
                    # Mettre à jour le solde du wallet (déduire le montant payé)
                    user_wallet.withdraw(amount_to_pay)
                    
                    # Calculate commission
                    from apps.users.models import User
                    import uuid
                    
                    business_location = tour.business_location
                    commission_amount = business_location.business.calculate_commission(amount_to_pay)
                    booking.commission_amount = commission_amount
                    
                    # Calculate net amount for business (amount_paid - commission)
                    net_amount = amount_to_pay - commission_amount
                    
                    # Get business location wallet
                    business_location_wallet = BusinessLocationWallet.objects.select_for_update().get(business_location=business_location)
                    
                    # Get super admin wallet
                    super_admin = User.objects.filter(is_superuser=True).first()
                    if not super_admin:
                        super_admin = User.objects.order_by('id').first()
                    
                    super_admin_wallet = getattr(super_admin, 'wallet', None)
                    
                    # Credit business location with net amount
                    if not business_location_wallet.deposit(net_amount):
                        raise ValidationError(f"Erreur lors du crédit du wallet business pour {business_location.name}.")
                    
                    # Create transaction for business location
                    business_transaction = UserTransaction.objects.create(
                        wallet=business_location_wallet,
                        transaction_type='PAYMENT',
                        amount=net_amount,
                        status='COMPLETED',
                        reference=str(uuid.uuid4()),
                        description=f"Paiement net tour '{tour.nom_balade}' (après commission)",
                        content_type=ContentType.objects.get_for_model(TourBooking),
                        object_id=booking.pk,
                        related_transaction=user_transaction
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
                            description=f"Commission tour '{tour.nom_balade}' - {business_location.name}",
                            content_type=ContentType.objects.get_for_model(TourBooking),
                            object_id=booking.pk,
                            created_at=timezone.now()
                        )
                    
                    # Lier les transactions
                    user_transaction.related_transaction = business_transaction
                    user_transaction.save()
                    
                    messages.success(request, _("Réservation créée avec succès ! Le paiement de {amount} FCFA a été traité (référence: {reference}). Nous vous contacterons bientôt pour confirmer les détails.").format(
                        amount=amount_to_pay,
                        reference=user_transaction.reference
                    ))
                    return redirect('tours:booking_detail', pk=booking.pk)
                
            except Exception as e:
                messages.error(request, _(f"Erreur lors de la création de la réservation : {str(e)}"))
                return redirect(request.path)
    else:
        # Pré-remplir les champs avec les données de l'utilisateur
        # Si first_name est vide, utiliser le username comme fallback
        first_name = request.user.first_name or request.user.username.split('_')[0] if request.user.username else ''
        
        initial_data = {
            'first_name': first_name,
            'email': request.user.email or '',
            'total_amount': tour.price_per_person  # Montant initial pour 1 participant
        }
        
        # Debug: Afficher les données utilisateur
        print(f"Debug - Données utilisateur:")
        print(f"  first_name: '{request.user.first_name}'")
        print(f"  email: '{request.user.email}'")
        print(f"  initial_data: {initial_data}")
        
        form = TourBookingForm(tour=tour, initial=initial_data)
    
    return render(request, 'tours/tour_booking_form.html', {
        'form': form,
        'tour': tour
    })

def tour_booking_list(request):
    """View for listing all tour bookings."""
    bookings = TourBooking.objects.all()
    
    return render(request, 'tours/booking_list.html', {
        'bookings': bookings
    })

@login_required
def tour_review_create(request, slug):
    """View for creating a tour review."""
    tour = get_object_or_404(Tour, slug=slug)
    
    # Check if user has completed a booking for this tour
    has_booking = TourBooking.objects.filter(
        tour=tour,
        customer=request.user,
        status='completed'
    ).exists()
    
    if not has_booking:
        messages.error(request, _('You can only review tours you have completed.'))
        return redirect('tours:tour_detail', slug=tour.slug)
    
    # Check if user has already reviewed this tour
    existing_review = TourReview.objects.filter(
        tour=tour,
        reviewer=request.user
    ).first()
    
    if existing_review:
        messages.error(request, _('You have already reviewed this tour.'))
        return redirect('tours:tour_detail', slug=tour.slug)
    
    if request.method == 'POST':
        form = TourReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.tour = tour
            review.reviewer = request.user
            review.save()
            messages.success(request, _('Review submitted successfully.'))
            return redirect('tours:tour_detail', slug=tour.slug)
    else:
        form = TourReviewForm()
    
    return render(request, 'tours/tour_review_form.html', {
        'form': form,
        'tour': tour
    })

def destination_detail(request, slug):
    """View for displaying destination details."""
    destination = get_object_or_404(TourDestination, slug=slug, is_active=True)
    nearby_destinations = destination.get_nearby_destinations()
    
    return render(request, 'tours/destination_detail.html', {
        'destination': destination,
        'nearby_destinations': nearby_destinations
    })

def activity_detail(request, slug):
    """View for displaying activity details."""
    activity = get_object_or_404(TourActivity, slug=slug, is_active=True)
    context = {'activity': activity}
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'tours/activity_detail_modal.html', context)
    return render(request, 'tours/activity_detail.html', context)

def destination_list(request):
    """View for listing all destinations."""
    destinations = TourDestination.objects.filter(is_active=True)
    
    return render(request, 'tours/destination_list.html', {
        'destinations': destinations
    })

@login_required
def destination_select(request):
    """View for selecting destinations when creating or editing tours."""
    tour_id = request.GET.get('tour')
    if not tour_id:
        messages.error(request, _('Tour ID is required.'))
        return redirect('home:home')
    
    try:
        tour = Tour.objects.get(pk=tour_id)
    except Tour.DoesNotExist:
        messages.error(request, _('Tour not found.'))
        return redirect('home:home')
    
    # Vérifier que l'utilisateur a accès à ce tour
    if request.user != tour.business_location.business.owner:
        messages.error(request, _('You do not have permission to select destinations for this tour.'))
        return redirect('tours:tour_detail', slug=tour.slug)
    
    # Get all available destinations
    available_destinations = TourDestination.objects.filter(is_active=True).exclude(tour=tour)
    selected_destinations = tour.destinations.filter(is_active=True)
    
    if request.method == 'POST':
        selected_destination_ids = request.POST.getlist('destinations')
        
        # Remove unselected destinations
        tour.destinations.remove(*selected_destinations.exclude(id__in=selected_destination_ids))
        
        # Add newly selected destinations
        new_destinations = TourDestination.objects.filter(id__in=selected_destination_ids)
        for destination in new_destinations:
            if destination not in tour.destinations.all():
                tour.destinations.add(destination)
        
        messages.success(request, _('Destinations updated successfully.'))
        return redirect('tours:tour_detail', slug=tour.slug)
    
    return render(request, 'tours/destination_select.html', {
        'tour': tour,
        'available_destinations': available_destinations,
        'selected_destinations': selected_destinations,
        'title': _('Select Destinations')
    })

def activity_list(request):
    """View for listing all activities."""
    activities = TourActivity.objects.filter(is_active=True)
    
    return render(request, 'tours/activity_list.html', {
        'activities': activities
    })

def tour_inquiry(request, slug):
    """View for handling tour inquiries."""
    tour = get_object_or_404(Tour, slug=slug, is_active=True)
    
    if request.method == 'POST':
        # Simple form handling for now
        messages.success(request, _('Your inquiry has been sent successfully. We will contact you soon.'))
        return redirect('tours:tour_detail', slug=tour.slug)
    
    return redirect('tours:tour_detail', slug=tour.slug)

@login_required
def activity_create(request):
    """View for creating a new tour activity."""
    # Récupérer l'ID du tour depuis les paramètres de requête
    tour_id = request.GET.get('tour')
    if not tour_id:
        messages.error(request, _('Tour ID is required.'))
        return redirect('home:home')
    
    try:
        tour = Tour.objects.get(pk=tour_id)
    except Tour.DoesNotExist:
        messages.error(request, _('Tour not found.'))
        return redirect('home:home')
    
    # Vérifier que l'utilisateur a accès à ce tour
    if request.user != tour.business_location.business.owner:
        messages.error(request, _('You do not have permission to create activities for this tour.'))
        return redirect('tours:tour_detail', slug=tour.slug)
    
    if request.method == 'POST':
        form = TourActivityForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                activity = form.save(commit=False)
                activity.tour = tour
                activity.save()
                messages.success(request, _('Activity created successfully.'))
                if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                    return HttpResponse('OK')
                return redirect('tours:tour_detail', slug=tour.slug)
            except Exception as e:
                messages.error(request, _(f'Error creating activity: {str(e)}'))
        else:
            messages.error(request, _('Please correct the errors below.'))
    else:
        form = TourActivityForm(initial={'tour': tour})
    context = {
        'form': form,
        'tour': tour,
        'title': _('Create Activity')
    }
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'tours/activity_form.html', context)
    return render(request, 'tours/activity_form.html', context)

@login_required
def activity_edit(request, slug):
    """View for editing an existing tour activity."""
    activity = get_object_or_404(TourActivity, slug=slug)
    
    if request.user != activity.tour.business_location.business.owner:
        messages.error(request, _('You do not have permission to edit this activity.'))
        return redirect('tours:activity_detail', slug=activity.slug)
    
    if request.method == 'POST':
        form = TourActivityForm(request.POST, request.FILES, instance=activity)
        if form.is_valid():
            activity = form.save()
            messages.success(request, _('Activity updated successfully.'))
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return HttpResponse('OK')
            return redirect('tours:tour_detail', slug=activity.tour.slug)
    else:
        form = TourActivityForm(instance=activity)
    context = {
        'form': form,
        'activity': activity,
        'tour': activity.tour,
        'title': _('Edit Activity')
    }
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return render(request, 'tours/activity_form.html', context)
    return render(request, 'tours/activity_form.html', context)

@login_required
def destination_create(request):
    """View for creating a new tour destination."""
    # Récupérer l'ID du tour depuis les paramètres de requête
    tour_id = request.GET.get('tour')
    if not tour_id:
        messages.error(request, _('Tour ID is required.'))
        return redirect('home:home')
    
    try:
        tour = Tour.objects.get(pk=tour_id)
    except Tour.DoesNotExist:
        messages.error(request, _('Tour not found.'))
        return redirect('home:home')
    
    # Vérifier que l'utilisateur a accès à ce tour
    if request.user != tour.business_location.business.owner:
        messages.error(request, _('You do not have permission to create destinations for this tour.'))
        return redirect('tours:tour_detail', slug=tour.slug)
    
    if request.method == 'POST':
        form = TourDestinationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                destination = form.save(commit=False)
                destination.tour = tour
                destination.save()
                messages.success(request, _('Destination created successfully.'))
                return redirect('tours:tour_detail', slug=tour.slug)
            except Exception as e:
                messages.error(request, _(f'Error creating destination: {str(e)}'))
        else:
            messages.error(request, _('Please correct the errors below.'))
    else:
        form = TourDestinationForm(initial={'tour': tour})
    
    return render(request, 'tours/destination_form.html', {
        'form': form,
        'tour': tour,
        'title': _('Create Destination')
    })

@login_required
def destination_edit(request, slug):
    """View for editing an existing tour destination."""
    destination = get_object_or_404(TourDestination, slug=slug)
    
    if request.user != destination.tour.business_location.business.owner:
        messages.error(request, _('You do not have permission to edit this destination.'))
        return redirect('tours:destination_detail', slug=destination.slug)
    
    if request.method == 'POST':
        form = TourDestinationForm(request.POST, request.FILES, instance=destination)
        if form.is_valid():
            destination = form.save()
            messages.success(request, _('Destination updated successfully.'))
            return redirect('tours:tour_detail', slug=destination.tour.slug)
    else:
        form = TourDestinationForm(instance=destination)
    
    return render(request, 'tours/destination_form.html', {
        'form': form,
        'destination': destination,
        'tour': destination.tour,
        'title': _('Edit Destination')
    })

@login_required
def activity_delete(request, slug):
    activity = get_object_or_404(TourActivity, slug=slug)
    # Vérifier que l'utilisateur a le droit de supprimer
    if request.user != activity.tour.business_location.business.owner:
        messages.error(request, _("Vous n'avez pas la permission de supprimer cette activité."))
        return redirect('tours:activity_detail', slug=activity.slug)
    if request.method == 'POST':
        business_location_pk = activity.tour.business_location.pk
        activity.delete()
        messages.success(request, _("Activité supprimée avec succès."))
        return redirect('business:business_location_dashboard', pk=business_location_pk)
    return redirect('tours:activity_detail', slug=activity.slug)

@login_required
def activity_select(request):
    """View for selecting activities when creating or editing tours."""
    tour_id = request.GET.get('tour')
    if not tour_id:
        messages.error(request, _('Tour ID is required.'))
        return redirect('home:home')
    try:
        tour = Tour.objects.get(pk=tour_id)
    except Tour.DoesNotExist:
        messages.error(request, _('Tour not found.'))
        return redirect('home:home')
    if request.user != tour.business_location.business.owner:
        messages.error(request, _('You do not have permission to select activities for this tour.'))
        return redirect('tours:tour_detail', slug=tour.slug)
    available_activities = TourActivity.objects.filter(is_active=True).exclude(tour=tour)
    selected_activities = tour.activities.filter(is_active=True)
    if request.method == 'POST':
        selected_activity_ids = request.POST.getlist('activities')
        tour.activities.remove(*selected_activities.exclude(id__in=selected_activity_ids))
        new_activities = TourActivity.objects.filter(id__in=selected_activity_ids)
        for activity in new_activities:
            if activity not in tour.activities.all():
                tour.activities.add(activity)
        messages.success(request, _('Activities updated successfully.'))
        return redirect('tours:tour_detail', slug=tour.slug)
    return render(request, 'tours/activity_select.html', {
        'tour': tour,
        'available_activities': available_activities,
        'selected_activities': selected_activities,
        'title': _('Select Activities')
    })

@login_required
def tour_booking_detail(request, pk):
    """Display booking details and allow final payment if needed."""
    booking = get_object_or_404(
        TourBooking,
        pk=pk,
        customer=request.user
    )
    
    # Calcul du montant total
    total_amount = booking.total_amount
    
    # Montant déjà payé (somme des transactions COMPLETED)
    already_paid = sum(
        t.amount for t in booking.transactions.filter(status='COMPLETED')
    )
    remaining_amount = total_amount - already_paid

    context = {
        'booking': booking,
        'total_amount': total_amount,
        'already_paid': already_paid,
        'remaining_amount': remaining_amount,
    }
    return render(request, 'tours/booking_detail.html', context)

@login_required
@require_POST
def tour_booking_payment(request, pk):
    """Permet à l'utilisateur de payer le solde restant d'une réservation de tour."""
    booking = get_object_or_404(
        TourBooking,
        pk=pk,
        customer=request.user
    )
    
    total_amount = booking.total_amount
    already_paid = sum(
        t.amount for t in booking.transactions.filter(status='COMPLETED')
    )
    remaining_amount = total_amount - already_paid

    if remaining_amount <= 0:
        messages.info(request, "Aucun montant restant à payer.")
        return redirect('tours:booking_detail', pk=pk)

    wallet = WalletService.get_user_wallet(request.user)
    if not wallet or not wallet.is_active:
        messages.error(request, "Votre wallet n'est pas actif.")
        return redirect('tours:booking_detail', pk=pk)

    if not WalletService.check_sufficient_funds(wallet, remaining_amount):
        messages.error(request, f"Solde insuffisant pour payer {remaining_amount:.0f} XAF.")
        return redirect('tours:booking_detail', pk=pk)

    try:
        with db_transaction.atomic():
            WalletService.update_wallet_balance(wallet, remaining_amount, 'subtract')
            # Créer la transaction
            transaction_obj = TransactionService.create_user_transaction(
                wallet=wallet,
                transaction_type='PAYMENT',
                amount=remaining_amount,
                description=f"Paiement réservation tour {booking.tour.nom_balade}",
                status='COMPLETED'
            )
            booking.transactions.add(transaction_obj)
            # Mettre à jour le statut si tout est payé
            booking.status = 'CONFIRMED'
            booking.save()
            messages.success(request, f"Paiement finalisé ! {remaining_amount:.0f} XAF ont été débités.")
    except Exception as e:
        messages.error(request, f"Erreur lors du paiement : {str(e)}")

    return redirect('tours:booking_detail', pk=pk)

def itinerary_list(request):
    """View for displaying itinerary planning page with map and form."""
    from apps.tourist_sites.models import ZoneDangereuse
    from apps.business.models import BusinessLocation
    
    # Récupérer tous les tours actifs pour le formulaire
    tours = Tour.objects.filter(is_active=True).order_by('nom_balade')
    
    # Récupérer les destinations pour la carte
    destinations = TourDestination.objects.filter(
        tour__is_active=True,
        is_active=True
    ).select_related('tour').order_by('tour__nom_balade', 'day_number')
    
    # Récupérer toutes les zones dangereuses
    zones_dangereuses = ZoneDangereuse.objects.filter(statut__in=['SIGNALEE', 'VERIFIEE'])
    zones_data = []
    for zone in zones_dangereuses:
        if zone.latitude and zone.longitude:
            zones_data.append({
                'id': zone.id_zonedangereuse,
                'name': zone.nom_zone,
                'description': zone.description_danger,
                'type_danger': zone.get_type_danger_display(),
                'latitude': float(zone.latitude),
                'longitude': float(zone.longitude),
                'likes': zone.get_likes_count(),
                'dislikes': zone.get_dislikes_count(),
                'site_name': zone.site.name if zone.site else 'Site non spécifié',
            })
    
    # Récupérer toutes les business locations
    business_locations = BusinessLocation.objects.filter(is_active=True)
    business_data = []
    for business in business_locations:
        if business.latitude and business.longitude:
            business_data.append({
                'id': business.id,
                'name': business.name,
                'business_type': business.business_location_type or 'other',
                'description': getattr(business, 'description', '') or '',
                'latitude': float(business.latitude),
                'longitude': float(business.longitude),
                'is_verified': business.is_verified,
                'rating': 0,  # Pas de système de rating pour l'instant
            })
    
    # Préparer les données pour la carte
    map_data = []
    for destination in destinations:
        if destination.latitude and destination.longitude:
            map_data.append({
                'name': destination.name,
                'tour_name': destination.tour.nom_balade,
                'tour_id': destination.tour.id,
                'description': destination.description,
                'day_number': destination.day_number,
                'latitude': float(destination.latitude),
                'longitude': float(destination.longitude),
                'image_url': destination.images.first().image.url if destination.images.exists() else None,
            })
    
    import json
    
    context = {
        'tours': tours,
        'map_data': json.dumps(map_data),
        'zones_data': json.dumps(zones_data),
        'business_data': json.dumps(business_data),
        'destinations': destinations,
    }
    
    return render(request, 'tours/itinerary_list.html', context)

@login_required
@require_POST
def vote_zone_dangereuse(request, zone_id):
    print(f'[DEBUG] Vote zone dangereuse - Zone ID: {zone_id}, User: {request.user}')
    user = request.user
    try:
        zone = ZoneDangereuse.objects.get(id_zonedangereuse=zone_id)
        print(f'[DEBUG] Zone trouvée: {zone.nom_zone}')
    except ZoneDangereuse.DoesNotExist:
        print(f'[DEBUG] Zone non trouvée pour ID: {zone_id}')
        return JsonResponse({'success': False, 'error': 'Zone dangereuse non trouvée.'}, status=404)
    
    try:
        import json
        data = json.loads(request.body)
        vote_type = data.get('vote')
        print(f'[DEBUG] Vote type reçu: {vote_type}')
        
        if vote_type not in ['like', 'dislike']:
            print(f'[DEBUG] Type de vote invalide: {vote_type}')
            return JsonResponse({'success': False, 'error': 'Type de vote invalide.'}, status=400)
        
        is_like = (vote_type == 'like')
        print(f'[DEBUG] is_like: {is_like}')
        
        try:
            # Essayer de créer ou mettre à jour le vote
            vote, created = ZoneDangereuseVote.objects.get_or_create(
                zone=zone, 
                utilisateur=user,
                defaults={'is_like': is_like}
            )
            
            if created:
                print(f'[DEBUG] Nouveau vote créé')
            else:
                # L'utilisateur a déjà voté, vérifier s'il change son vote
                if vote.is_like == is_like:
                    print(f'[DEBUG] Utilisateur a déjà voté de cette façon')
                    return JsonResponse({'success': False, 'error': 'Vous avez déjà voté de cette façon pour cette zone.'}, status=400)
                else:
                    # Changer le vote
                    print(f'[DEBUG] Changement de vote de {vote.is_like} vers {is_like}')
                    vote.is_like = is_like
                    vote.save()
            
            # Vérifier le seuil de validation
            zone.check_validation(seuil=3)
            
            likes = zone.get_likes_count()
            dislikes = zone.get_dislikes_count()
            print(f'[DEBUG] Résultat - Likes: {likes}, Dislikes: {dislikes}')
            
            return JsonResponse({
                'success': True,
                'likes': likes,
                'dislikes': dislikes,
                'message': 'Vote enregistré.'
            })
            
        except Exception as vote_error:
            print(f'[DEBUG] Erreur lors de la création/mise à jour du vote: {str(vote_error)}')
            return JsonResponse({'success': False, 'error': f'Erreur lors du vote: {str(vote_error)}'}, status=500)
            
    except Exception as e:
        print(f'[DEBUG] Erreur lors du vote: {str(e)}')
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
