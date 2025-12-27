from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator
from django.db.models import Avg, Count
from django.views.decorators.http import require_http_methods
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.conf import settings
from django.views.decorators.http import require_GET, require_POST
from django.core.exceptions import ValidationError
import json
from decimal import Decimal
from datetime import date
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
import uuid

from ..models import Room, RoomBooking, RoomType, RoomImage
from ..forms import RoomSearchForm, RoomBookingForm
from ..services.room_service import RoomService
from ..services.reservation_service import ReservationService
from apps.business.models import BusinessLocation
from apps.business.models.business_amenity import BusinessAmenityCategory
from apps.wallets.services.wallet_service import WalletService
from apps.wallets.services.transaction_service import TransactionService
from apps.wallets.models.wallet import UserWallet, BusinessWallet, BusinessLocationWallet
from apps.wallets.models.transaction import UserTransaction
from apps.users.models import User
from django.contrib.contenttypes.models import ContentType


def general_room_list(request):
    """Display list of available rooms from all business locations with advanced filtering."""
    queryset = Room.objects.filter(
        is_available=True,
        maintenance_mode=False,
        business_location__is_active=True
    ).select_related(
        'room_type',
        'business_location',
        'business_location__business'
    ).prefetch_related('images')
    
    # Apply filters from GET parameters
    # Room type filter
    room_type_id = request.GET.get('room_type')
    if room_type_id:
        queryset = queryset.filter(room_type_id=room_type_id)
    
    # Price range filter
    price_range = request.GET.get('price_range')
    if price_range:
        if price_range == '0-10000':
            queryset = queryset.filter(price_per_night__lte=10000)
        elif price_range == '10000-25000':
            queryset = queryset.filter(price_per_night__gte=10000, price_per_night__lte=25000)
        elif price_range == '25000-50000':
            queryset = queryset.filter(price_per_night__gte=25000, price_per_night__lte=50000)
        elif price_range == '50000-100000':
            queryset = queryset.filter(price_per_night__gte=50000, price_per_night__lte=100000)
        elif price_range == '100000+':
            queryset = queryset.filter(price_per_night__gte=100000)
    
    # Min/Max price filter
    min_price = request.GET.get('min_price')
    if min_price:
        queryset = queryset.filter(price_per_night__gte=min_price)
    
    max_price = request.GET.get('max_price')
    if max_price:
        queryset = queryset.filter(price_per_night__lte=max_price)
    
    # Capacity filter
    capacity = request.GET.get('capacity')
    if capacity:
        if capacity == '1':
            queryset = queryset.filter(max_occupancy=1)
        elif capacity == '2':
            queryset = queryset.filter(max_occupancy=2)
        elif capacity == '3-4':
            queryset = queryset.filter(max_occupancy__gte=3, max_occupancy__lte=4)
        elif capacity == '5+':
            queryset = queryset.filter(max_occupancy__gte=5)
    
    # Guests filter
    guests = request.GET.get('guests')
    if guests:
        queryset = queryset.filter(max_occupancy__gte=int(guests))
    
    # Business location filter
    business_location_id = request.GET.get('business_location')
    if business_location_id:
        queryset = queryset.filter(business_location_id=business_location_id)
    
    # Floor filter
    floor = request.GET.get('floor')
    if floor:
        if floor == '0':
            queryset = queryset.filter(floor=0)
        elif floor == '1':
            queryset = queryset.filter(floor=1)
        elif floor == '2':
            queryset = queryset.filter(floor=2)
        elif floor == '3':
            queryset = queryset.filter(floor=3)
        elif floor == '4+':
            queryset = queryset.filter(floor__gte=4)
    
    # Date availability filter
    check_in_date = request.GET.get('check_in_date')
    check_out_date = request.GET.get('check_out_date')
    if check_in_date and check_out_date:
        queryset = queryset.exclude(
            bookings__status__in=['CONFIRMED', 'CHECKED_IN'],
            bookings__check_in_date__lte=check_out_date,
            bookings__check_out_date__gte=check_in_date
        )
    
    # Amenities filter
    amenities = request.GET.getlist('amenities')
    if amenities:
        for amenity_id in amenities:
            queryset = queryset.filter(amenities__contains=[amenity_id])
    
    # Sort options
    sort = request.GET.get('sort', 'name')
    if sort == 'price':
        queryset = queryset.order_by('price_per_night')
    elif sort == '-price':
        queryset = queryset.order_by('-price_per_night')
    elif sort == 'capacity':
        queryset = queryset.order_by('max_occupancy')
    elif sort == 'created':
        queryset = queryset.order_by('-created_at')
    else:
        queryset = queryset.order_by('room_number')
    
    # Pagination
    per_page = int(request.GET.get('per_page', 12))
    paginator = Paginator(queryset, per_page)
    page = request.GET.get('page')
    rooms = paginator.get_page(page)
    
    # Get filter options
    room_types = RoomType.objects.filter(is_active=True)
    business_locations = BusinessLocation.objects.filter(is_active=True)
    amenities_by_category = get_amenities_by_category()
    
    context = {
        'rooms': rooms,
        'room_types': room_types,
        'business_locations': business_locations,
        'amenities_by_category': amenities_by_category,
        'is_general_list': True,
    }
    return render(request, 'rooms/room_list.html', context)


def room_list(request, business_location_id):
    """Display list of available rooms for a specific business location with filtering."""
    queryset = Room.objects.filter(
        is_available=True,
        maintenance_mode=False,
        business_location_id=business_location_id,
        business_location__is_active=True
    ).select_related(
        'room_type',
        'business_location',
        'business_location__business'
    ).prefetch_related('images')
    
    # Apply filters from GET parameters (same as general_room_list but for specific location)
    # Room type filter
    room_type_id = request.GET.get('room_type')
    if room_type_id:
        queryset = queryset.filter(room_type_id=room_type_id)
    
    # Price range filter
    price_range = request.GET.get('price_range')
    if price_range:
        if price_range == '0-10000':
            queryset = queryset.filter(price_per_night__lte=10000)
        elif price_range == '10000-25000':
            queryset = queryset.filter(price_per_night__gte=10000, price_per_night__lte=25000)
        elif price_range == '25000-50000':
            queryset = queryset.filter(price_per_night__gte=25000, price_per_night__lte=50000)
        elif price_range == '50000-100000':
            queryset = queryset.filter(price_per_night__gte=50000, price_per_night__lte=100000)
        elif price_range == '100000+':
            queryset = queryset.filter(price_per_night__gte=100000)
    
    # Min/Max price filter
    min_price = request.GET.get('min_price')
    if min_price:
        queryset = queryset.filter(price_per_night__gte=min_price)
    
    max_price = request.GET.get('max_price')
    if max_price:
        queryset = queryset.filter(price_per_night__lte=max_price)
    
    # Capacity filter
    capacity = request.GET.get('capacity')
    if capacity:
        if capacity == '1':
            queryset = queryset.filter(max_occupancy=1)
        elif capacity == '2':
            queryset = queryset.filter(max_occupancy=2)
        elif capacity == '3-4':
            queryset = queryset.filter(max_occupancy__gte=3, max_occupancy__lte=4)
        elif capacity == '5+':
            queryset = queryset.filter(max_occupancy__gte=5)
    
    # Guests filter
    guests = request.GET.get('guests')
    if guests:
        queryset = queryset.filter(max_occupancy__gte=int(guests))
    
    # Floor filter
    floor = request.GET.get('floor')
    if floor:
        if floor == '0':
            queryset = queryset.filter(floor=0)
        elif floor == '1':
            queryset = queryset.filter(floor=1)
        elif floor == '2':
            queryset = queryset.filter(floor=2)
        elif floor == '3':
            queryset = queryset.filter(floor=3)
        elif floor == '4+':
            queryset = queryset.filter(floor__gte=4)
    
    # Date availability filter
    check_in_date = request.GET.get('check_in_date')
    check_out_date = request.GET.get('check_out_date')
    if check_in_date and check_out_date:
        queryset = queryset.exclude(
            bookings__status__in=['CONFIRMED', 'CHECKED_IN'],
            bookings__check_in_date__lte=check_out_date,
            bookings__check_out_date__gte=check_in_date
        )
    
    # Amenities filter
    amenities = request.GET.getlist('amenities')
    if amenities:
        for amenity_id in amenities:
            queryset = queryset.filter(amenities__contains=[amenity_id])
    
    # Sort options
    sort = request.GET.get('sort', 'name')
    if sort == 'price':
        queryset = queryset.order_by('price_per_night')
    elif sort == '-price':
        queryset = queryset.order_by('-price_per_night')
    elif sort == 'capacity':
        queryset = queryset.order_by('max_occupancy')
    elif sort == 'created':
        queryset = queryset.order_by('-created_at')
    else:
        queryset = queryset.order_by('room_number')
    
    # Pagination
    per_page = int(request.GET.get('per_page', 12))
    paginator = Paginator(queryset, per_page)
    page = request.GET.get('page')
    rooms = paginator.get_page(page)
    
    # Get filter options
    room_types = RoomType.objects.filter(is_active=True)
    business_location = get_object_or_404(BusinessLocation, id=business_location_id)
    amenities_by_category = get_amenities_by_category()
    
    context = {
        'rooms': rooms,
        'room_types': room_types,
        'business_location': business_location,
        'business_location_id': business_location_id,
        'amenities_by_category': amenities_by_category,
        'is_general_list': False,
    }
    return render(request, 'rooms/room_list.html', context)


@login_required
def room_create(request, business_location_id):
    """Create a new room without Django form validation."""
    business_location = get_object_or_404(BusinessLocation, id=business_location_id)
    
    # Check if user is the owner
    if business_location.business.owner != request.user:
        messages.error(request, _('You do not have permission to create rooms for this business.'))
        return redirect('rooms:room_list', business_location_id=business_location_id)
    
    if request.method == 'POST':
        # Récupération des données POST
        room_type_id = request.POST.get('room_type')
        room_number = request.POST.get('room_number', '').strip()
        floor = request.POST.get('floor')
        description = request.POST.get('description', '').strip()
        price_per_night = request.POST.get('price_per_night')
        max_occupancy = request.POST.get('max_occupancy')
        amenities = request.POST.getlist('amenities')
        is_available = request.POST.get('is_available') == 'on'
        maintenance_mode = request.POST.get('maintenance_mode') == 'on'
        
        # Validation manuelle
        errors = []
        
        # Validation du type de chambre
        if not room_type_id:
            errors.append(_('Le type de chambre est requis.'))
        else:
            try:
                room_type = RoomType.objects.get(id=room_type_id, is_active=True)
            except RoomType.DoesNotExist:
                errors.append(_('Type de chambre invalide.'))
        
        # Validation du numéro de chambre
        if not room_number:
            errors.append(_('Le numéro de chambre est requis.'))
        else:
            # Vérifier l'unicité du numéro de chambre
            if Room.objects.filter(business_location=business_location, room_number=room_number).exists():
                errors.append(_('Ce numéro de chambre existe déjà dans cet établissement.'))
        
        # Validation du prix
        if not price_per_night:
            errors.append(_('Le prix par nuit est requis.'))
        else:
            try:
                price = Decimal(price_per_night)
                if price <= 0:
                    errors.append(_('Le prix doit être supérieur à 0.'))
            except (ValueError, TypeError):
                errors.append(_('Le prix doit être un nombre valide.'))
        
        # Validation de la capacité
        if not max_occupancy:
            errors.append(_('La capacité maximale est requise.'))
        else:
            try:
                occupancy = int(max_occupancy)
                if occupancy <= 0:
                    errors.append(_('La capacité doit être supérieure à 0.'))
            except (ValueError, TypeError):
                errors.append(_('La capacité doit être un nombre entier valide.'))
        
        # Validation de l'étage
        floor_value = None
        if floor:
            try:
                floor_value = int(floor)
                if floor_value < 0:
                    errors.append(_('L\'étage ne peut pas être négatif.'))
            except (ValueError, TypeError):
                errors.append(_('L\'étage doit être un nombre entier valide.'))
        
        # Si pas d'erreurs, créer la chambre
        if not errors:
            try:
                room = Room.objects.create(
                    business_location=business_location,
                    room_type=room_type,
                    room_number=room_number,
                    floor=floor_value,
                    description=description,
                    price_per_night=price,
                    max_occupancy=occupancy,
                    amenities=amenities if amenities else None,
                    is_available=is_available,
                    maintenance_mode=maintenance_mode
                )
                
                # Associer les images temporaires à la chambre
                associate_temp_images(request, room)
                
                messages.success(request, _('Chambre créée avec succès!'))
                return redirect('business:location_detail', pk=business_location.id)
                
            except Exception as e:
                errors.append(_('Erreur lors de la création de la chambre: ') + str(e))
        
        # Si erreurs, afficher les messages
        for error in errors:
            messages.error(request, error)
    
    context = {
        'title': _('Nouvelle Chambre'),
        'business_location_id': business_location_id,
        'business_location_name': business_location.name,
        'room_types': RoomType.objects.filter(is_active=True),
        'amenities_by_category': get_amenities_by_category(),
        'selected_amenities': [],
        'is_new_room': True,
    }
    
    # Nettoyer les images temporaires orphelines
    cleanup_temp_images(request)
    
    return render(request, 'rooms/room_form.html', context)


@login_required
def room_edit(request, pk):
    """Update an existing room without Django form validation."""
    room = get_object_or_404(Room, pk=pk)
    
    # Check if user is the owner
    if room.business_location.business.owner != request.user:
        messages.error(request, _('You do not have permission to edit this room.'))
        return redirect('rooms:room_list', business_location_id=room.business_location.id)
    
    if request.method == 'POST':
        # Récupération des données POST
        room_type_id = request.POST.get('room_type')
        room_number = request.POST.get('room_number', '').strip()
        floor = request.POST.get('floor')
        description = request.POST.get('description', '').strip()
        price_per_night = request.POST.get('price_per_night')
        max_occupancy = request.POST.get('max_occupancy')
        amenities = request.POST.getlist('amenities')
        is_available = request.POST.get('is_available') == 'on'
        maintenance_mode = request.POST.get('maintenance_mode') == 'on'
        
        # Validation manuelle
        errors = []
        
        # Validation du type de chambre
        if not room_type_id:
            errors.append(_('Le type de chambre est requis.'))
        else:
            try:
                room_type = RoomType.objects.get(id=room_type_id, is_active=True)
            except RoomType.DoesNotExist:
                errors.append(_('Type de chambre invalide.'))
        
        # Validation du numéro de chambre
        if not room_number:
            errors.append(_('Le numéro de chambre est requis.'))
        else:
            # Vérifier l'unicité du numéro de chambre (exclure la chambre actuelle)
            if Room.objects.filter(
                business_location=room.business_location, 
                room_number=room_number
            ).exclude(id=room.id).exists():
                errors.append(_('Ce numéro de chambre existe déjà dans cet établissement.'))
        
        # Validation du prix
        if not price_per_night:
            errors.append(_('Le prix par nuit est requis.'))
        else:
            try:
                price = Decimal(price_per_night)
                if price <= 0:
                    errors.append(_('Le prix doit être supérieur à 0.'))
            except (ValueError, TypeError):
                errors.append(_('Le prix doit être un nombre valide.'))
        
        # Validation de la capacité
        if not max_occupancy:
            errors.append(_('La capacité maximale est requise.'))
        else:
            try:
                occupancy = int(max_occupancy)
                if occupancy <= 0:
                    errors.append(_('La capacité doit être supérieure à 0.'))
            except (ValueError, TypeError):
                errors.append(_('La capacité doit être un nombre entier valide.'))
        
        # Validation de l'étage
        floor_value = None
        if floor:
            try:
                floor_value = int(floor)
                if floor_value < 0:
                    errors.append(_('L\'étage ne peut pas être négatif.'))
            except (ValueError, TypeError):
                errors.append(_('L\'étage doit être un nombre entier valide.'))
        
        # Si pas d'erreurs, mettre à jour la chambre
        if not errors:
            try:
                room.room_type = room_type
                room.room_number = room_number
                room.floor = floor_value
                room.description = description
                room.price_per_night = price
                room.max_occupancy = occupancy
                room.amenities = amenities if amenities else None
                room.is_available = is_available
                room.maintenance_mode = maintenance_mode
                room.save()
                
                # Handle image uploads and deletions (pour chambres existantes)
                handle_image_uploads(request, room)
                handle_image_deletions(request, room)
                
                messages.success(request, _('Chambre mise à jour avec succès!'))
                return redirect('rooms:room_list', business_location_id=room.business_location.id)
                
            except Exception as e:
                errors.append(_('Erreur lors de la mise à jour de la chambre: ') + str(e))
        
        # Si erreurs, afficher les messages
        for error in errors:
            messages.error(request, error)
    
    context = {
        'room': room,
        'title': f'Modifier la Chambre - {room.room_number}',
        'business_location_id': room.business_location.id,
        'business_location_name': room.business_location.name,
        'room_types': RoomType.objects.filter(is_active=True),
        'amenities_by_category': get_amenities_by_category(),
        'selected_amenities': room.amenities or [],
        'is_new_room': False,
    }
    return render(request, 'rooms/room_form.html', context)


def room_detail(request, pk):
    """Display room details."""
    room = get_object_or_404(
        Room.objects.select_related(
            'room_type',
            'business_location',
            'business_location__business'
        ).prefetch_related('images'),
        pk=pk
    )
    
    # Get similar rooms (same room type, same business location, different room)
    similar_rooms = Room.objects.filter(
        room_type=room.room_type,
        business_location=room.business_location,
        is_available=True,
        maintenance_mode=False
    ).exclude(pk=room.pk).select_related(
        'room_type',
        'business_location'
    ).prefetch_related('images')[:6]
    
    # Get other room types from the same business location
    other_room_types = RoomType.objects.filter(
        rooms__business_location=room.business_location,
        rooms__is_available=True,
        rooms__maintenance_mode=False
    ).exclude(pk=room.room_type.pk).distinct()[:4]
    
    # Create search form for booking
    search_form = RoomSearchForm(initial={
        'check_in_date': request.GET.get('check_in_date'),
        'check_out_date': request.GET.get('check_out_date'),
        'guests': request.GET.get('guests', room.max_occupancy)
    })
    
    today = date.today()
    
    context = {
        'room': room,
        'similar_rooms': similar_rooms,
        'other_room_types': other_room_types,
        'search_form': search_form,
        'today': today,
    }
    return render(request, 'rooms/room_detail.html', context)


@login_required
def room_booking_create(request, room_id):
    """Create new room booking avec paiement partiel via wallet utilisateur."""
    room = get_object_or_404(Room, pk=room_id)
    total_amount = None
    check_in_date = None
    check_out_date = None
    if request.method == 'POST':
        form = RoomBookingForm(request.POST)
        payment_percentage = request.POST.get('payment_percentage')
        try:
            payment_percentage = int(payment_percentage)
            if payment_percentage not in [20, 50, 100]:
                raise ValueError
        except Exception:
            messages.error(request, _("Pourcentage de paiement invalide."))
            return redirect(request.path)
        if form.is_valid():
            check_in_date = form.cleaned_data['check_in_date']
            check_out_date = form.cleaned_data['check_out_date']
            d1 = check_in_date
            d2 = check_out_date
            nights = (d2 - d1).days
            if nights <= 0:
                messages.error(request, _("La durée de séjour doit être d'au moins 1 nuit."))
                return redirect(request.path)
            total_amount = room.price_per_night * nights
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
                with transaction.atomic():
                    # Débiter le wallet
                    WalletService.update_wallet_balance(wallet, amount_to_pay, 'subtract')
                    
                    # Calculate commission
                    business_location = room.business_location
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
                    
                    # Credit super admin with commission
                    if commission_amount > 0 and super_admin_wallet:
                        if not super_admin_wallet.deposit(commission_amount):
                            raise ValidationError("Erreur lors du crédit de la commission au wallet admin.")
                    
                    # Créer la réservation directement (statut PENDING) avec commission
                    nights = (check_out_date - check_in_date).days
                    total_amount = room.price_per_night * nights
                    
                    booking = RoomBooking.objects.create(
                        room=room,
                        customer=request.user,
                        business_location=room.business_location,
                        check_in_date=check_in_date,
                        check_out_date=check_out_date,
                        adults_count=form.cleaned_data['adults_count'],
                        children_count=form.cleaned_data['children_count'],
                        hotel_notes=form.cleaned_data['hotel_notes'],
                        status='PENDING',
                        special_requests=form.cleaned_data.get('special_requests'),
                        customer_notes=form.cleaned_data.get('customer_notes'),
                        commission_amount=commission_amount,
                        total_amount=total_amount
                    )
                    
                    # Create transaction for business location
                    UserTransaction.objects.create(
                        wallet=business_wallet,
                        transaction_type='HOLD',
                        amount=net_amount,
                        status='COMPLETED',
                        reference=str(uuid.uuid4()),
                        description=f"Paiement partiel chambre {room.room_number} (après commission)",
                        content_type=ContentType.objects.get_for_model(booking),
                        object_id=booking.id,
                        created_at=timezone.now()
                    )
                    
                    # Create commission transaction
                    if commission_amount > 0 and super_admin_wallet:
                        UserTransaction.objects.create(
                            wallet=super_admin_wallet,
                            transaction_type='COMMISSION',
                            amount=commission_amount,
                            status='COMPLETED',
                            reference=str(uuid.uuid4()),
                            description=f"Commission réservation chambre {room.room_number}",
                            content_type=ContentType.objects.get_for_model(booking),
                            object_id=booking.id,
                            created_at=timezone.now()
                        )
                    
                    # Créer la transaction HOLD pour l'utilisateur
                    description = f"Réservation chambre {room.room_number} ({payment_percentage}% du montant total)"
                    user_transaction = UserTransaction.objects.create(
                        wallet=wallet,
                        transaction_type='HOLD',
                        amount=amount_to_pay,
                        status='COMPLETED',
                        reference=str(uuid.uuid4()),
                        description=description,
                        content_type=ContentType.objects.get_for_model(booking),
                        object_id=booking.id,
                        created_at=timezone.now()
                    )
                    
                    messages.success(request, _(f"Réservation créée avec succès ! {amount_to_pay:.0f} XAF ont été débités de votre wallet."))
                    return redirect('rooms:booking_detail', reference=booking.booking_reference)
            except Exception as e:
                messages.error(request, _(f"Erreur lors du paiement ou de la réservation : {str(e)}"))
                return redirect(request.path)
        else:
            check_in_date = form.data.get('check_in_date')
            check_out_date = form.data.get('check_out_date')
    else:
        form = RoomBookingForm()
        check_in_date = request.GET.get('check_in_date')
        check_out_date = request.GET.get('check_out_date')
    # Calcul du montant total si les dates sont présentes
    from datetime import datetime
    try:
        if check_in_date and check_out_date:
            d1 = datetime.strptime(str(check_in_date), '%Y-%m-%d').date()
            d2 = datetime.strptime(str(check_out_date), '%Y-%m-%d').date()
            nights = (d2 - d1).days
            if nights > 0:
                total_amount = room.price_per_night * nights
    except Exception:
        total_amount = None
    context = {
        'form': form,
        'room': room,
        'check_in_date': check_in_date,
        'check_out_date': check_out_date,
        'duration_nights': nights if check_in_date and check_out_date and 'nights' in locals() else '',
        'total_amount': total_amount,
    }
    return render(request, 'rooms/booking_form.html', context)


@login_required
def booking_detail(request, reference):
    """Display booking details and allow final payment if needed."""
    booking = get_object_or_404(
        RoomBooking,
        booking_reference=reference,
        customer=request.user
    )
    # Calcul du montant total
    nights = (booking.check_out_date - booking.check_in_date).days
    total_amount = booking.room.price_per_night * nights

    # Montant déjà payé (somme des transactions HOLD/COMPLETED)
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
    return render(request, 'rooms/booking_detail.html', context)


@login_required
@require_POST
def finalize_payment(request, reference):
    """Permet à l'utilisateur de payer le solde restant d'une réservation."""
    booking = get_object_or_404(
        RoomBooking,
        booking_reference=reference,
        customer=request.user
    )
    nights = (booking.check_out_date - booking.check_in_date).days
    total_amount = booking.room.price_per_night * nights
    already_paid = sum(
        t.amount for t in booking.transactions.filter(status='COMPLETED')
    )
    remaining_amount = total_amount - already_paid

    if remaining_amount <= 0:
        messages.info(request, "Aucun montant restant à payer.")
        return redirect('rooms:booking_detail', reference=reference)

    wallet = WalletService.get_user_wallet(request.user)
    if not wallet or not wallet.is_active:
        messages.error(request, "Votre wallet n'est pas actif.")
        return redirect('rooms:booking_detail', reference=reference)

    if not WalletService.check_sufficient_funds(wallet, remaining_amount):
        messages.error(request, f"Solde insuffisant pour payer {remaining_amount:.0f} XAF.")
        return redirect('rooms:booking_detail', reference=reference)

    try:
        with transaction.atomic():
            WalletService.update_wallet_balance(wallet, remaining_amount, 'subtract')
            # Créer la transaction
            transaction_obj = TransactionService.create_user_transaction(
                wallet=wallet,
                transaction_type='PAYMENT',
                amount=remaining_amount,
                description=f"Solde réservation chambre {booking.room.room_number}",
                status='COMPLETED'
            )
            booking.transactions.add(transaction_obj)
            # Mettre à jour le statut si tout est payé
            booking.status = 'CONFIRMED'
            booking.save()
            messages.success(request, f"Paiement finalisé ! {remaining_amount:.0f} XAF ont été débités.")
    except Exception as e:
        messages.error(request, f"Erreur lors du paiement : {str(e)}")

    return redirect('rooms:booking_detail', reference=reference)


@login_required
def finalize_payment_admin(request, reference):
    """Affiche la page de finalisation du paiement en espèces avec modale de confirmation."""
    booking = get_object_or_404(RoomBooking, booking_reference=reference)
    
    # Vérifier que l'utilisateur est le propriétaire de l'hôtel
    if booking.business_location.business.owner != request.user:
        messages.error(request, "Vous n'avez pas l'autorisation de finaliser cette transaction.")
        return redirect('rooms:booking_list', business_location_id=booking.business_location.id)
    
    # Vérifier que la réservation est en attente
    if booking.status != 'PENDING':
        messages.error(request, "Cette réservation n'est pas en attente de paiement.")
        return redirect('rooms:booking_list', business_location_id=booking.business_location.id)
    
    # Récupérer la transaction HOLD originale
    hold_transaction = booking.transactions.filter(transaction_type='HOLD', status='COMPLETED').first()
    if not hold_transaction:
        messages.error(request, "Aucune transaction HOLD trouvée pour cette réservation.")
        return redirect('rooms:booking_list', business_location_id=booking.business_location.id)
    
    hold_amount = hold_transaction.amount
    total_amount = booking.total_amount
    remaining_amount = total_amount - hold_amount

    if remaining_amount <= 0:
        messages.info(request, "Aucun montant restant à payer.")
        return redirect('rooms:booking_list', business_location_id=booking.business_location.id)

    context = {
        'booking': booking,
        'hold_amount': hold_amount,
        'remaining_amount': remaining_amount,
        'total_amount': total_amount,
    }
    return render(request, 'rooms/finalize_payment_admin.html', context)


@login_required
@require_POST
def process_cash_payment(request, reference):
    """Traite le paiement en espèces et approuve la réservation avec nouvelle logique de transactions."""
    booking = get_object_or_404(RoomBooking, booking_reference=reference)
    
    # Vérifier que l'utilisateur est le propriétaire de l'hôtel
    if booking.business_location.business.owner != request.user:
        messages.error(request, "Vous n'avez pas l'autorisation de finaliser cette transaction.")
        return redirect('rooms:booking_list', business_location_id=booking.business_location.id)
    
    # Vérifier que la réservation est en attente
    if booking.status != 'PENDING':
        messages.error(request, "Cette réservation n'est pas en attente de paiement.")
        return redirect('rooms:booking_list', business_location_id=booking.business_location.id)
    
    # Récupérer la transaction HOLD originale
    hold_transaction = booking.transactions.filter(transaction_type='HOLD', status='COMPLETED').first()
    if not hold_transaction:
        messages.error(request, "Aucune transaction HOLD trouvée pour cette réservation.")
        return redirect('rooms:booking_list', business_location_id=booking.business_location.id)
    
    hold_amount = hold_transaction.amount
    total_amount = booking.total_amount
    remaining_amount = total_amount - hold_amount

    try:
        with transaction.atomic():
            # 1. Rembourser le montant HOLD au wallet utilisateur
            customer_wallet = WalletService.get_user_wallet(booking.customer)
            if customer_wallet and customer_wallet.is_active:
                customer_wallet.deposit(hold_amount)
                
                # Créer une transaction de remboursement pour le HOLD
                refund_transaction = UserTransaction.objects.create(
                    wallet=customer_wallet,
                    transaction_type='REFUND',
                    amount=hold_amount,
                    description=f"Remboursement transaction HOLD - Réservation chambre {booking.room.room_number}",
                    status='COMPLETED',
                    reference=f"REFUND-HOLD-{booking.booking_reference}-{uuid.uuid4().hex[:8]}",
                    content_object=booking
                )
                booking.transactions.add(refund_transaction)
            
            # 2. Créer une nouvelle transaction PAYMENT avec le montant HOLD
            payment_transaction = UserTransaction.objects.create(
                wallet=customer_wallet,
                transaction_type='PAYMENT',
                amount=hold_amount,
                description=f"Paiement finalisé - Réservation chambre {booking.room.room_number} (montant HOLD)",
                status='COMPLETED',
                reference=f"PAY-HOLD-{booking.booking_reference}-{uuid.uuid4().hex[:8]}",
                content_object=booking
            )
            booking.transactions.add(payment_transaction)
            
            # 3. Créer une transaction CASH_PAYMENT pour le reste du montant
            if remaining_amount > 0:
                cash_payment_transaction = UserTransaction.objects.create(
                    wallet=customer_wallet,
                    transaction_type='CASH_PAYMENT',
                    amount=remaining_amount,
                    description=f"Paiement en espèces - Réservation chambre {booking.room.room_number} (reste)",
                    status='COMPLETED',
                    reference=f"PAY-CASH-{booking.booking_reference}-{uuid.uuid4().hex[:8]}",
                    content_object=booking
                )
                booking.transactions.add(cash_payment_transaction)
            
            # 4. Calculate commission and update business location wallet
            business_location = booking.business_location
            commission_amount = business_location.business.calculate_commission(total_amount)
            booking.commission_amount = commission_amount
            
            # Calculate net amount for business (total - commission)
            net_amount = total_amount - commission_amount
            
            business_location_wallet = getattr(booking.business_location, 'wallet', None)
            if business_location_wallet:
                # Credit business location with net amount
                business_location_wallet.deposit(net_amount)
                
                # Create transaction for business location
                business_transaction = UserTransaction.objects.create(
                    wallet=business_location_wallet,
                    transaction_type='PAYMENT',
                    amount=net_amount,
                    description=f"Paiement net reçu - Réservation chambre {booking.room.room_number} (après commission)",
                    status='COMPLETED',
                    reference=f"PAY-BUSINESS-{booking.booking_reference}-{uuid.uuid4().hex[:8]}",
                    content_object=booking
                )
                booking.transactions.add(business_transaction)
            
            # 5. Credit super admin with commission
            from apps.users.models import User
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
                    reference=f"COM-ROOM-{booking.booking_reference}-{uuid.uuid4().hex[:8]}",
                    description=f"Commission réservation chambre {booking.room.room_number} - {business_location.name}",
                    content_object=booking
                )
            
            # 5. Marquer la transaction HOLD comme CANCELLED
            hold_transaction.status = 'CANCELLED'
            hold_transaction.save()
            
            # 6. Mettre à jour le statut de la réservation
            booking.status = 'CONFIRMED'
            booking.save()
            
            messages.success(request, f"Paiement finalisé avec succès ! Montant HOLD: {hold_amount:.0f} XAF, Reste en espèces: {remaining_amount:.0f} XAF. Total: {total_amount:.0f} XAF.")
            
    except Exception as e:
        messages.error(request, f"Erreur lors de la finalisation : {str(e)}")

    return redirect('rooms:booking_list', business_location_id=booking.business_location.id)


@login_required
@require_POST
def approve_booking(request, reference):
    """Approuve une réservation en utilisant la nouvelle logique de transactions."""
    booking = get_object_or_404(RoomBooking, booking_reference=reference)
    
    # Vérifier que l'utilisateur est le propriétaire de l'hôtel
    if booking.business_location.business.owner != request.user:
        messages.error(request, "Vous n'avez pas l'autorisation d'approuver cette réservation.")
        return redirect('rooms:booking_list', business_location_id=booking.business_location.id)
    
    # Vérifier que la réservation est en attente
    if booking.status != 'PENDING':
        messages.error(request, "Cette réservation n'est pas en attente d'approbation.")
        return redirect('rooms:booking_list', business_location_id=booking.business_location.id)
    
    # Récupérer la transaction HOLD originale
    hold_transaction = booking.transactions.filter(transaction_type='HOLD', status='COMPLETED').first()
    if not hold_transaction:
        messages.error(request, "Aucune transaction HOLD trouvée pour cette réservation.")
        return redirect('rooms:booking_list', business_location_id=booking.business_location.id)
    
    hold_amount = hold_transaction.amount
    total_amount = booking.total_amount
    
    # Si le montant HOLD ne couvre pas le total, rediriger vers la finalisation du paiement
    if hold_amount < total_amount:
        return redirect('rooms:finalize_payment_admin', reference=reference)
    
    # Sinon, approuver directement la réservation avec la nouvelle logique
    try:
        with transaction.atomic():
            # 1. Rembourser le montant HOLD au wallet utilisateur
            customer_wallet = WalletService.get_user_wallet(booking.customer)
            if customer_wallet and customer_wallet.is_active:
                customer_wallet.deposit(hold_amount)
                
                # Créer une transaction de remboursement pour le HOLD
                refund_transaction = UserTransaction.objects.create(
                    wallet=customer_wallet,
                    transaction_type='REFUND',
                    amount=hold_amount,
                    description=f"Remboursement transaction HOLD - Réservation chambre {booking.room.room_number}",
                    status='COMPLETED',
                    reference=f"REFUND-HOLD-{booking.booking_reference}-{uuid.uuid4().hex[:8]}",
                    content_object=booking
                )
                booking.transactions.add(refund_transaction)
            
            # 2. Créer une nouvelle transaction PAYMENT avec le montant HOLD
            payment_transaction = UserTransaction.objects.create(
                wallet=customer_wallet,
                transaction_type='PAYMENT',
                amount=hold_amount,
                description=f"Paiement finalisé - Réservation chambre {booking.room.room_number} (montant HOLD)",
                status='COMPLETED',
                reference=f"PAY-HOLD-{booking.booking_reference}-{uuid.uuid4().hex[:8]}",
                content_object=booking
            )
            booking.transactions.add(payment_transaction)
            
            # 3. Mettre à jour le wallet de l'établissement
            business_location_wallet = getattr(booking.business_location, 'wallet', None)
            if business_location_wallet:
                # Ajouter le montant total au wallet de l'établissement
                business_location_wallet.deposit(total_amount)
                
                # Créer la transaction pour l'établissement
                business_transaction = UserTransaction.objects.create(
                    wallet=business_location_wallet,
                    transaction_type='PAYMENT',
                    amount=total_amount,
                    description=f"Paiement total reçu - Réservation chambre {booking.room.room_number} - Client: {booking.customer.get_full_name()} (Total: {total_amount:.0f} XAF)",
                    status='COMPLETED',
                    reference=f"PAY-BUSINESS-{booking.booking_reference}-{uuid.uuid4().hex[:8]}",
                    content_object=booking
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
    
    return redirect('rooms:booking_list', business_location_id=booking.business_location.id)


@login_required
@require_POST
def cancel_booking(request, reference):
    """Annule une réservation de chambre avec remboursement et commissions selon le délai."""
    booking = get_object_or_404(RoomBooking, booking_reference=reference, customer=request.user)
    now = timezone.now().date()
    if booking.check_in_date <= now:
        messages.error(request, "Impossible d'annuler une réservation déjà commencée ou passée.")
        return redirect('users:user_booking_list')
    reason = request.POST.get('reason', '').strip()
    if not reason:
        messages.error(request, "Veuillez fournir une raison d'annulation.")
        return redirect('users:user_booking_list')
    already_paid = sum(t.amount for t in booking.transactions.filter(status='COMPLETED'))
    # Calcul du délai
    delta = booking.check_in_date - now
    refund_amount = already_paid
    commission_business = 0
    commission_admin = 0
    # Trouver le wallet business location
    business_location_wallet = getattr(booking.business_location, 'wallet', None)
    # Trouver le wallet super admin (premier user)
    from apps.users.models import User
    super_admin = User.objects.order_by('id').first()
    super_admin_wallet = getattr(super_admin, 'wallet', None)
    # Trouver le wallet utilisateur
    user_wallet = UserWallet.objects.filter(user=request.user).first()
    # Si annulation < 24h, appliquer commissions
    if delta < timedelta(days=1):
        commission_business = already_paid * 0.09
        commission_admin = already_paid * 0.01
        refund_amount = already_paid - commission_business - commission_admin
    # Remboursement utilisateur
    if refund_amount > 0 and user_wallet:
        user_wallet.deposit(refund_amount)
        UserTransaction.objects.create(
            wallet=user_wallet,
            transaction_type='REFUND',
            amount=refund_amount,
            status='COMPLETED',
            description=f"Remboursement annulation réservation {booking.booking_reference}",
            content_object=booking,
            reference=f"REFUND-{booking.booking_reference}-{uuid.uuid4().hex[:8]}"
        )
    # Commission business location
    if commission_business > 0 and business_location_wallet:
        business_location_wallet.deposit(commission_business)
        UserTransaction.objects.create(
            wallet=business_location_wallet,
            transaction_type='COMMISSION',
            amount=commission_business,
            status='COMPLETED',
            description=f"Commission annulation réservation {booking.booking_reference}",
            content_object=booking,
            reference=f"COM-BUSINESSLOC-{booking.booking_reference}-{uuid.uuid4().hex[:8]}"
        )
    # Commission super admin
    if commission_admin > 0 and super_admin_wallet:
        super_admin_wallet.deposit(commission_admin)
        UserTransaction.objects.create(
            wallet=super_admin_wallet,
            transaction_type='COMMISSION',
            amount=commission_admin,
            status='COMPLETED',
            description=f"Commission admin annulation réservation {booking.booking_reference}",
            content_object=booking,
            reference=f"COM-ADMIN-{booking.booking_reference}-{uuid.uuid4().hex[:8]}"
        )
    # Statut et raison
    booking.status = 'CANCELLED'
    booking.cancellation_reason = reason
    booking.cancelled_at = timezone.now()
    booking.save()
    messages.success(request, f"Votre réservation a été annulée. Remboursement : {refund_amount:.0f} XAF.{' Commissions prélevées.' if commission_business or commission_admin else ''}")
    return redirect('users:user_booking_list')


# Fonctions utilitaires
def get_amenities_by_category():
    """Get amenities organized by category."""
    categories = BusinessAmenityCategory.objects.filter(is_active=True).prefetch_related('amenities')
    amenities_by_category = {}
    for category in categories:
        amenities_by_category[category] = category.amenities.filter(is_active=True)
    return amenities_by_category


def cleanup_temp_images(request):
    """Nettoie les images temporaires orphelines de la session"""
    temp_ids = request.session.get('room_temp_images', [])
    if temp_ids:
        # Supprimer les images qui ne sont plus dans la session
        orphaned_images = RoomImage.objects.filter(room=None).exclude(id__in=temp_ids)
        for img in orphaned_images:
            try:
                img.image.delete(save=False)
                img.delete()
            except Exception:
                pass


def associate_temp_images(request, room):
    """Associe les images temporaires à la chambre créée"""
    temp_ids = request.session.get('room_temp_images', [])
    if temp_ids:
        images = RoomImage.objects.filter(id__in=temp_ids, room=None)
        for img in images:
            img.room = room
            img.save()
        
        # Nettoyer la session
        del request.session['room_temp_images']


def handle_image_uploads(request, room):
    """Handle multiple image uploads for existing rooms."""
    images = request.FILES.getlist('images')
    current_count = room.images.count()
    
    for i, image in enumerate(images):
        if current_count + i < 10:  # Max 10 images
            RoomImage.objects.create(
                room=room,
                image=image,
                order=current_count + i
            )


def handle_image_deletions(request, room):
    """Handle image deletions for existing rooms."""
    delete_images = request.POST.getlist('delete_images')
    for image_id in delete_images:
        try:
            image = RoomImage.objects.get(id=image_id, room=room)
            image.delete()
        except RoomImage.DoesNotExist:
            pass


# Vues AJAX pour les images
@login_required
@require_POST
def upload_room_image(request, room_id):
    """Upload a room image via AJAX for existing rooms."""
    try:
        room = get_object_or_404(Room, id=room_id)
        
        # Check if user has permission to edit this room
        if room.business_location.business.owner != request.user:
            return JsonResponse({
                'success': False,
                'error': 'Permission denied'
            }, status=403)
        
        # Check if image was provided
        if 'image' not in request.FILES:
            return JsonResponse({
                'success': False,
                'error': 'Aucune image fournie'
            }, status=400)
        
        image_file = request.FILES['image']
        
        # Validate file type
        allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
        if image_file.content_type not in allowed_types:
            return JsonResponse({
                'success': False,
                'error': 'Type de fichier non supporté. Utilisez JPEG, PNG, GIF ou WebP.'
            }, status=400)
        
        # Validate file size (5MB max)
        if image_file.size > 5 * 1024 * 1024:
            return JsonResponse({
                'success': False,
                'error': 'La taille du fichier ne doit pas dépasser 5MB.'
            }, status=400)
        
        # Check if we haven't reached the limit
        current_count = room.images.count()
        if current_count >= 10:
            return JsonResponse({
                'success': False,
                'error': 'Vous ne pouvez pas ajouter plus de 10 images.'
            }, status=400)
        
        # Create the image
        caption = request.POST.get('caption', '')
        room_image = RoomImage.objects.create(
            room=room,
            image=image_file,
            caption=caption,
            order=current_count
        )
        
        return JsonResponse({
            'success': True,
            'image_id': room_image.id,
            'image_url': room_image.image.url,
            'caption': room_image.caption,
            'order': room_image.order
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors de l\'upload: {str(e)}'
        }, status=500)


@login_required
@require_POST
def delete_room_image(request, room_id, image_id):
    """Delete a room image via AJAX for existing rooms."""
    try:
        room = get_object_or_404(Room, id=room_id)
        
        # Check if user has permission to edit this room
        if room.business_location.business.owner != request.user:
            return JsonResponse({
                'success': False,
                'error': 'Permission denied'
            }, status=403)
        
        image = get_object_or_404(RoomImage, id=image_id, room=room)
        image.delete()
        
        # Reorder remaining images
        for i, remaining_image in enumerate(room.images.all().order_by('order')):
            remaining_image.order = i
            remaining_image.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Image supprimée avec succès'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors de la suppression: {str(e)}'
        }, status=500)


@login_required
@require_POST
def reorder_room_images(request, room_id):
    """Reorder room images via AJAX for existing rooms."""
    try:
        room = get_object_or_404(Room, id=room_id)
        
        # Check if user has permission to edit this room
        if room.business_location.business.owner != request.user:
            return JsonResponse({
                'success': False,
                'error': 'Permission denied'
            }, status=403)
        
        data = json.loads(request.body)
        image_orders = data.get('image_orders', [])
        
        # Update order for each image
        for item in image_orders:
            image_id = item.get('image_id')
            new_order = item.get('order')
            
            if image_id and new_order is not None:
                try:
                    image = RoomImage.objects.get(id=image_id, room=room)
                    image.order = new_order
                    image.save()
                except RoomImage.DoesNotExist:
                    continue
        
        return JsonResponse({
            'success': True,
            'message': 'Ordre des images mis à jour'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Erreur lors du réordonnancement: {str(e)}'
        }, status=500)


@csrf_exempt
@login_required
def upload_image_temp(request):
    """Upload temporaire d'images pour nouvelles chambres (stockage en session)"""
    if request.method != 'POST' or 'image' not in request.FILES:
        return JsonResponse({'success': False, 'error': 'Méthode invalide ou fichier manquant.'})
    
    image = request.FILES['image']
    
    # Validation du fichier
    allowed_types = ['image/jpeg', 'image/jpg', 'image/png', 'image/gif', 'image/webp']
    if image.content_type not in allowed_types:
        return JsonResponse({
            'success': False,
            'error': 'Type de fichier non supporté. Utilisez JPEG, PNG, GIF ou WebP.'
        })
    
    # Validation de la taille (5MB max)
    if image.size > 5 * 1024 * 1024:
        return JsonResponse({
            'success': False,
            'error': 'La taille du fichier ne doit pas dépasser 5MB.'
        })
    
    # Vérifier la limite d'images temporaires
    temp_ids = request.session.get('room_temp_images', [])
    if len(temp_ids) >= 10:
        return JsonResponse({
            'success': False,
            'error': 'Vous ne pouvez pas ajouter plus de 10 images.'
        })
    
    # Créer une instance temporaire (room=None)
    temp_img = RoomImage.objects.create(
        room=None,
        image=image,
        caption='',
        order=len(temp_ids)
    )
    
    # Stocker l'ID dans la session
    temp_ids.append(temp_img.id)
    request.session['room_temp_images'] = temp_ids
    
    return JsonResponse({
        'success': True, 
        'id': temp_img.id, 
        'url': temp_img.image.url,
        'order': temp_img.order
    })


@csrf_exempt
@login_required
def delete_image_temp(request, image_id):
    """Suppression d'image temporaire"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode invalide.'})
    
    temp_ids = request.session.get('room_temp_images', [])
    if image_id in temp_ids:
        try:
            img = RoomImage.objects.get(id=image_id, room=None)
            img.image.delete(save=False)
            img.delete()
            temp_ids.remove(image_id)
            request.session['room_temp_images'] = temp_ids
            
            # Réordonner les images restantes
            remaining_images = RoomImage.objects.filter(id__in=temp_ids, room=None).order_by('order')
            for i, remaining_img in enumerate(remaining_images):
                remaining_img.order = i
                remaining_img.save()
            
            return JsonResponse({'success': True})
        except RoomImage.DoesNotExist:
            pass
    
    return JsonResponse({'success': False, 'error': 'Image non trouvée.'})


@login_required
def list_image_temp(request):
    """Liste des images temporaires"""
    temp_ids = request.session.get('room_temp_images', [])
    images = RoomImage.objects.filter(id__in=temp_ids, room=None).order_by('order')
    data = [
        {
            'id': img.id,
            'url': img.image.url,
            'caption': img.caption,
            'order': img.order
        }
        for img in images
    ]
    return JsonResponse({'images': data})


def room_search(request):
    """Advanced room search page."""
    # Get filter options for the search form
    room_types = RoomType.objects.filter(is_active=True)
    business_locations = BusinessLocation.objects.filter(is_active=True)
    amenities_by_category = get_amenities_by_category()
    
    context = {
        'room_types': room_types,
        'business_locations': business_locations,
        'amenities_by_category': amenities_by_category,
    }
    return render(request, 'rooms/room_search.html', context)


def room_type_list(request, business_location_id):
    """
    Affiche la liste des types de chambres pour une business location.
    """
    room_types = RoomType.objects.filter(business_location_id=business_location_id)
    context = {
        'room_types': room_types,
        'business_location_id': business_location_id,
    }
    return render(request, 'rooms/room_type_list.html', context)


def booking_list(request, business_location_id):
    """
    Affiche la liste des réservations pour toutes les chambres d'une business location.
    """
    rooms = Room.objects.filter(business_location_id=business_location_id)
    bookings = RoomBooking.objects.filter(room__in=rooms).order_by('-created_at')
    context = {
        'bookings': bookings,
        'business_location_id': business_location_id,
    }
    return render(request, 'rooms/booking_list.html', context)
