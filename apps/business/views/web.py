from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator
from django.db.models import Avg, Count, Sum
from django.core.validators import URLValidator
from django.core.exceptions import ValidationError
from datetime import datetime, date, timedelta
from django.views.decorators.http import require_http_methods, require_POST
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.storage import default_storage
from django.conf import settings
import os
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from apps.wallets.models.transaction import UserTransaction
import uuid
from decimal import Decimal
import json
from dateutil.relativedelta import relativedelta

from ..models import (
    Business,
    BusinessLocation,
    BusinessLocationImage,
    BusinessReview,
    BusinessHours,
    BusinessAmenityCategory,
    BusinessAmenity,
    BusinessAmenityAssignment
)
from ..forms import (
    BusinessForm,
    BusinessLocationForm,
    BusinessLocationImageForm,
    BusinessHoursForm,
    BusinessReviewForm,
    BusinessAmenityCategoryForm,
    BusinessAmenityForm,
    BusinessAmenityAssignmentForm,
    BusinessSearchForm
)
from apps.orders.models.order import RestaurantOrder, OrderItem
from apps.orders.forms import CustomRestaurantOrderForm, OrderCustomerForm
from apps.users.models.user import User
from django.urls import reverse
from apps.orders.models.menu_item import MenuItem
from apps.tours.models import Tour, TourDestination, TourBooking, TourReview, TourSchedule

def business_list(request):
    """
    Display list of businesses with search and filtering
    """
    form = BusinessSearchForm(request.GET)
    businesses = Business.objects.all()
    
    if form.is_valid():
        query = form.cleaned_data.get('query')
        business_type = form.cleaned_data.get('business_type')
        rating = form.cleaned_data.get('rating')
        sort_by = form.cleaned_data.get('sort_by')
        verified_only = form.cleaned_data.get('verified_only')
        
        if query:
            businesses = businesses.filter(name__icontains=query)
        
        if business_type:
            businesses = businesses.filter(
                locations__business_location_type=business_type
            ).distinct()
        
        if rating:
            businesses = businesses.filter(
                reviews__overall_rating__gte=rating
            ).distinct()
        
        if verified_only:
            businesses = businesses.filter(is_verified=True)
        
        if sort_by == 'rating':
            businesses = businesses.annotate(
                avg_rating=Avg('reviews__overall_rating')
            ).order_by('-avg_rating')
        elif sort_by == 'reviews':
            businesses = businesses.annotate(
                review_count=Count('reviews')
            ).order_by('-review_count')
        else:  # name or default
            businesses = businesses.order_by('name')
    
    # Add annotations for display
    businesses = businesses.annotate(
        avg_rating=Avg('reviews__overall_rating'),
        review_count=Count('reviews')
    )
    
    # Pagination
    paginator = Paginator(businesses, 12)  # Show 12 businesses per page
    page = request.GET.get('page')
    businesses = paginator.get_page(page)
    
    context = {
        'form': form,
        'businesses': businesses,
    }
    return render(request, 'business/business_list.html', context)

def business_detail(request, pk):
    """
    Affiche le détail d'un business avec toutes les infos nécessaires pour un affichage moderne et complet.
    """
    business = get_object_or_404(Business, pk=pk)
    user = request.user
    is_owner = (user == business.owner)

    # Images du business (carousel)
    images = business.images.all() if hasattr(business, 'images') else []

    # Locations (avec image principale, statuts, etc.)
    locations = business.locations.all().prefetch_related('images')
    location_cards = []
    for location in locations:
        primary_image = location.images.filter(is_primary=True).first() or location.images.first()
        image_url = primary_image.image.url if primary_image else '/static/vendor/fontawesome/svgs/solid/building.svg'
        location_cards.append({
            'location': location,
            'image_url': image_url,
            'is_active': location.is_active,
            'is_verified': location.is_verified,
            'is_main_location': location.is_main_location,
            'is_owner': is_owner,
        })

    # Horaires du business principal (on prend la main location si dispo, sinon la première)
    main_location = locations.filter(is_main_location=True).first() or locations.first()
    hours = {}
    current_day = None
    if main_location:
        from apps.business.models.business_hours import BusinessHours
        import datetime
        days_of_week = dict(BusinessHours.DAYS_OF_WEEK)
        for day_num, day_name in BusinessHours.DAYS_OF_WEEK:
            schedule = main_location.business_hours.filter(day=day_num).first()
            hours[day_name] = schedule
        current_day = datetime.datetime.now().weekday()
    else:
        days_of_week = {}

    # Amenities par catégorie
    amenities = {}
    if main_location:
        assignments = main_location.amenity_assignments.select_related('amenity__category').filter(is_active=True)
        for assign in assignments:
            cat = assign.amenity.category
            if cat not in amenities:
                amenities[cat] = []
            amenities[cat].append(assign)

    # Stats de rating (pour le business global)
    from apps.business.models.business_review import BusinessReview
    rating_stats = BusinessReview.objects.filter(
        business_location__business=business,
        is_approved=True
    ).aggregate(
        avg_overall=Avg('rating'),
        avg_service=Avg('service_rating'),
        avg_value=Avg('value_rating'),
        avg_cleanliness=Avg('cleanliness_rating'),
        avg_location=Avg('location_rating'),
        total_reviews=Count('id')
    )

    avg = rating_stats.get('avg_overall') or 0
    stars_count = int(round(avg))
    stars_range = range(stars_count)

    context = {
        'business': business,
        'is_owner': is_owner,
        'images': images,
        'location_cards': location_cards,
        'main_location': main_location,
        'hours': hours,
        'current_day': current_day,
        'amenities': amenities,
        'rating_stats': rating_stats,
        'stars_range': stars_range,
        'days_of_week': days_of_week,
    }
    return render(request, 'business/business_detail.html', context)

@login_required
def business_create(request):
    """
    Create a new business profile with manual validation
    """
    if request.method == 'POST':
        # Get form data
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        website = request.POST.get('website', '').strip()
        description = request.POST.get('description', '').strip()
        founded_date = request.POST.get('founded_date', '').strip()

        # Validation
        errors = []

        # Required fields validation
        if not name:
            errors.append(_("Le nom de l'entreprise est requis."))
        if not email:
            errors.append(_("L'email est requis."))
        if not phone:
            errors.append(_("Le numéro de téléphone est requis."))
        if not description:
            errors.append(_("La description est requise."))

        # Email validation
        if email and '@' not in email:
            errors.append(_("L'adresse email n'est pas valide."))

        # Phone validation (Cameroon format)
        if phone:
            phone = phone.replace(' ', '').replace('-', '')
            if not phone.isdigit() or len(phone) != 9 or not phone[0] in '6':
                errors.append(_("Le numéro de téléphone doit contenir 9 chiffres et commencer par 6."))

        # Website validation
        if website:
            try:
                URLValidator()(website)
            except ValidationError:
                errors.append(_("L'URL du site web n'est pas valide."))

        # Founded date validation
        if founded_date:
            try:
                founded_date = datetime.strptime(founded_date, '%Y-%m-%d').date()
                if founded_date > datetime.now().date():
                    errors.append(_("La date de création ne peut pas être dans le futur."))
            except ValueError:
                errors.append(_("Le format de la date de création n'est pas valide."))
        else:
            founded_date = None

        if errors:
            for error in errors:
                messages.error(request, error)
            context = {
                'title': _('Create Business Profile'),
                'business': None,
                'main_location': None,
                'form_data': {
                    'name': name,
                    'email': email,
                    'phone': phone,
                    'website': website,
                    'description': description,
                    'founded_date': founded_date,
                }
            }
            return render(request, 'business/business_form.html', context)

        try:
            # Create business
            business = Business.objects.create(
                name=name,
                email=email,
                phone=f"+237{phone}",  # Add Cameroon prefix
                website=website,
                description=description,
                founded_date=founded_date,
                owner=request.user
            )
            
            # Gestion des documents uploadés
            document_title = request.POST.get('document_title', '').strip()
            document_type = request.POST.get('document_type', 'other')
            document_description = request.POST.get('document_description', '').strip()
            document_file = request.FILES.get('document_file')
            
            if document_file and document_title:
                from apps.business.models.business_location import BusinessLocationDocument, BusinessLocation
                # Créer une localisation principale pour stocker le document
                main_location = BusinessLocation.objects.create(
                    business=business,
                    name=f"Localisation principale de {business.name}",
                    description="Localisation créée automatiquement pour les documents",
                    is_main_location=True,
                    owner=request.user
                )
                
                BusinessLocationDocument.objects.create(
                    business_location=main_location,
                    file=document_file,
                    title=document_title,
                    description=document_description,
                    document_type=document_type
                )
            
            messages.success(request, _('Entreprise créée avec succès.'))
            return redirect('business:business_detail', pk=business.pk)

        except Exception as e:
            messages.error(request, _("Une erreur s'est produite lors de la création de l'entreprise."))
            context = {
                'title': _('Create Business Profile'),
                'business': None,
                'main_location': None,
                'form_data': {
                    'name': name,
                    'email': email,
                    'phone': phone,
                    'website': website,
                    'description': description,
                    'founded_date': founded_date,
                }
            }
            return render(request, 'business/business_form.html', context)

    # Initial form display (GET request)
    context = {
        'title': _('Create Business Profile'),
        'business': None,
        'main_location': None,
        'form_data': {
            'name': '',
            'email': '',
            'phone': '',
            'website': '',
            'description': '',
            'founded_date': None,
        }
    }
    return render(request, 'business/business_form.html', context)

@login_required
def business_edit(request, pk):
    """
    Edit business profile with document upload support
    """
    business = get_object_or_404(Business, pk=pk)
    
    # Check if user is the owner
    if business.owner != request.user:
        messages.error(request, _('You do not have permission to edit this business.'))
        return redirect('business:business-detail', pk=business.pk)
    
    if request.method == 'POST':
        # Traitement des données du formulaire principal
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        phone = request.POST.get('phone', '').strip()
        website = request.POST.get('website', '').strip()
        description = request.POST.get('description', '').strip()
        founded_date = request.POST.get('founded_date', '').strip()

        # Validation
        errors = []
        if not name:
            errors.append(_("Le nom de l'entreprise est requis."))
        if not email:
            errors.append(_("L'email est requis."))
        if not phone:
            errors.append(_("Le numéro de téléphone est requis."))
        if not description:
            errors.append(_("La description est requise."))

        # Email validation
        if email and '@' not in email:
            errors.append(_("L'adresse email n'est pas valide."))

        # Phone validation (Cameroon format)
        if phone:
            phone = phone.replace(' ', '').replace('-', '')
            if not phone.isdigit() or len(phone) != 9 or not phone[0] in '6':
                errors.append(_("Le numéro de téléphone doit contenir 9 chiffres et commencer par 6."))

        # Website validation
        if website:
            try:
                URLValidator()(website)
            except ValidationError:
                errors.append(_("L'URL du site web n'est pas valide."))

        # Founded date validation
        if founded_date:
            try:
                founded_date = datetime.strptime(founded_date, '%Y-%m-%d').date()
                if founded_date > datetime.now().date():
                    errors.append(_("La date de création ne peut pas être dans le futur."))
            except ValueError:
                errors.append(_("Le format de la date de création n'est pas valide."))
        else:
            founded_date = None
    
        if errors:
            for error in errors:
                messages.error(request, error)
            context = {
                'title': _('Edit Business Profile'),
                'business': business,
                'main_location': business.locations.filter(is_main_location=True).first() if business else None,
                'form_data': {
                    'name': name,
                    'email': email,
                    'phone': phone,
                    'website': website,
                    'description': description,
                    'founded_date': founded_date,
                }
            }
            return render(request, 'business/business_form.html', context)

        try:
            # Mettre à jour l'entreprise
            business.name = name
            business.email = email
            business.phone = f"+237{phone}"
            business.website = website
            business.description = description
            business.founded_date = founded_date
            business.save()
            
            # Gestion des documents uploadés
            document_title = request.POST.get('document_title', '').strip()
            document_type = request.POST.get('document_type', 'other')
            document_description = request.POST.get('document_description', '').strip()
            document_file = request.FILES.get('document_file')
            
            if document_file and document_title:
                from apps.business.models.business_location import BusinessLocationDocument
                # Chercher la localisation principale ou créer une temporaire
                main_location = business.locations.filter(is_main_location=True).first()
                if not main_location:
                    # Créer une localisation temporaire pour stocker le document
                    from apps.business.models.business_location import BusinessLocation
                    main_location = BusinessLocation.objects.create(
                        business=business,
                        name=f"Localisation principale de {business.name}",
                        description="Localisation créée automatiquement pour les documents",
                        is_main_location=True,
                        owner=request.user
                    )
                
                BusinessLocationDocument.objects.create(
                    business_location=main_location,
                    file=document_file,
                    title=document_title,
                    description=document_description,
                    document_type=document_type
                )
            
            messages.success(request, _('Profil de l\'entreprise mis à jour avec succès.'))
            return redirect('business:business_detail', pk=business.pk)

        except Exception as e:
            messages.error(request, _("Une erreur s'est produite lors de la mise à jour de l'entreprise."))
            context = {
        'title': _('Edit Business Profile'),
                'business': business,
                'main_location': business.locations.filter(is_main_location=True).first() if business else None,
                'form_data': {
                    'name': name,
                    'email': email,
                    'phone': phone,
                    'website': website,
                    'description': description,
                    'founded_date': founded_date,
                }
            }
            return render(request, 'business/business_form.html', context)
    
    # Initial form display (GET request)
    context = {
        'title': _('Edit Business Profile'),
        'business': business,
        'main_location': business.locations.filter(is_main_location=True).first() if business else None,
        'form_data': {
            'name': business.name,
            'email': business.email,
            'phone': business.phone[4:] if business.phone.startswith('+237') else business.phone,
            'website': business.website or '',
            'description': business.description,
            'founded_date': business.founded_date,
        }
    }
    return render(request, 'business/business_form.html', context)

@login_required
def location_create(request, business_pk):
    """
    Create a new business location
    """
    business = get_object_or_404(Business, pk=business_pk)
    
    # Check if user is the owner
    if business.owner != request.user:
        messages.error(request, _('You do not have permission to add locations.'))
        return redirect('business:business-detail', pk=business.pk)
    
    if request.method == 'POST':
        form = BusinessLocationForm(request.POST)
        if form.is_valid():
            location = form.save(commit=False)
            location.business = business
            location.save()
            messages.success(request, _('Business location created successfully.'))
            return redirect('business:business-detail', pk=business.pk)
    else:
        form = BusinessLocationForm()
    
    context = {
        'form': form,
        'business': business,
        'title': _('Add Business Location'),
    }
    return render(request, 'business/location_form.html', context)

@login_required
def location_edit(request, pk):
    """
    Edit business location
    """
    location = get_object_or_404(BusinessLocation, pk=pk)
    
    # Check if user is the owner
    if location.business.owner != request.user:
        messages.error(request, _('You do not have permission to edit this location.'))
        return redirect('business:business-detail', pk=location.business.pk)
    
    if request.method == 'POST':
        form = BusinessLocationForm(request.POST, instance=location)
        if form.is_valid():
            form.save()
            messages.success(request, _('Business location updated successfully.'))
            return redirect('business:business-detail', pk=location.business.pk)
    else:
        form = BusinessLocationForm(instance=location)
    
    context = {
        'form': form,
        'location': location,
        'title': _('Edit Business Location'),
    }
    return render(request, 'business/location_form.html', context)

@login_required
def location_image_upload(request, location_pk):
    """
    Upload business location images
    """
    location = get_object_or_404(BusinessLocation, pk=location_pk)
    
    # Check if user is the owner
    if location.business.owner != request.user:
        messages.error(request, _('You do not have permission to upload images.'))
        return redirect('business:business-detail', pk=location.business.pk)
    
    if request.method == 'POST':
        form = BusinessLocationImageForm(request.POST, request.FILES)
        if form.is_valid():
            image = form.save(commit=False)
            image.business_location = location
            image.save()
            messages.success(request, _('Image uploaded successfully.'))
            return redirect('business:business-detail', pk=location.business.pk)
    else:
        form = BusinessLocationImageForm()
    
    context = {
        'form': form,
        'location': location,
        'images': location.images.all(),
    }
    return render(request, 'business/location_image_form.html', context)

@login_required
def location_hours_edit(request, location_pk):
    """
    Edit business location operating hours
    """
    location = get_object_or_404(BusinessLocation, pk=location_pk)
    
    # Check if user is the owner
    if location.business.owner != request.user:
        messages.error(request, _('You do not have permission to edit business hours.'))
        return redirect('business:business-detail', pk=location.business.pk)
    
    # Get or create hours for each day
    hours_by_day = {}
    for day in range(7):  # 0 = Monday, 6 = Sunday
        hours, created = BusinessHours.objects.get_or_create(
            business_location=location,
            day=day
        )
        hours_by_day[day] = hours
    
    if request.method == 'POST':
        forms = {
            day: BusinessHoursForm(request.POST, prefix=str(day), instance=hours)
            for day, hours in hours_by_day.items()
        }
        
        if all(form.is_valid() for form in forms.values()):
            for form in forms.values():
                form.save()
            messages.success(request, _('Business hours updated successfully.'))
            return redirect('business:business-detail', pk=location.business.pk)
    else:
        forms = {
            day: BusinessHoursForm(prefix=str(day), instance=hours)
            for day, hours in hours_by_day.items()
        }
    
    context = {
        'location': location,
        'forms': forms,
        'days': BusinessHours.DAYS_OF_WEEK,
    }
    return render(request, 'business/location_hours_form.html', context)

@login_required
def add_review(request, pk):
    """
    Add a review for a business
    """
    business = get_object_or_404(Business, pk=pk)
    
    # Check if user is not the owner
    if business.owner == request.user:
        messages.error(request, _('You cannot review your own business.'))
        return redirect('business:business-detail', pk=business.pk)
    
    if request.method == 'POST':
        form = BusinessReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.business = business
            review.reviewer = request.user
            review.save()
            messages.success(request, _('Your review has been submitted.'))
            return redirect('business:business-detail', pk=business.pk)
    else:
        form = BusinessReviewForm()
    
    context = {
        'form': form,
        'business': business,
    }
    return render(request, 'business/review_form.html', context)

@login_required
def location_detail(request, pk):
    """
    Affiche le détail d'une business_location avec ses statuts, infos et entités liées selon le type.
    """
    location = get_object_or_404(BusinessLocation, pk=pk)
    business = location.business
    user_is_owner = (request.user == business.owner)

    # Préparation des entités liées selon le type
    rooms = vehicles = tours = orders = None
    if location.business_location_type == 'hotel':
        rooms = location.rooms.all() if hasattr(location, 'rooms') else None
    elif location.business_location_type == 'transport':
        vehicles = location.vehicles.all() if hasattr(location, 'vehicles') else None
    elif location.business_location_type == 'tour_operator':
        tours = location.tours.all() if hasattr(location, 'tours') else None
    elif location.business_location_type == 'restaurant':
        orders = location.restaurant_orders_from_location.all() if hasattr(location, 'restaurant_orders_from_location') else None

    context = {
        'location': location,
        'business': business,
        'user_is_owner': user_is_owner,
        'rooms': rooms,
        'vehicles': vehicles,
        'tours': tours,
        'orders': orders,
    }
    return render(request, 'business/location_detail.html', context)

@login_required
def my_businesses(request):
    """
    Display all businesses owned by the current user and accessible locations
    """
    import sys
    print("=" * 50, file=sys.stderr)
    print("=== VUE my_businesses APPELEE ===", file=sys.stderr)
    print("=" * 50, file=sys.stderr)
    
    # Entreprises dont l'utilisateur est propriétaire
    owned_businesses = Business.objects.filter(owner=request.user)
    
    # Debug: afficher les informations de l'utilisateur et des entreprises
    print(f"=== DEBUG my_businesses ===", file=sys.stderr)
    print(f"User: {request.user.username} (ID: {request.user.id})", file=sys.stderr)
    print(f"User is authenticated: {request.user.is_authenticated}", file=sys.stderr)
    print(f"Owned businesses count: {owned_businesses.count()}", file=sys.stderr)
    for business in owned_businesses:
        print(f"  - Business: {business.name} (ID: {business.id})", file=sys.stderr)
    
    # Établissements auxquels l'utilisateur a accès via des permissions
    try:
        from apps.business.views.permissions import get_accessible_locations
        accessible_locations = get_accessible_locations(request.user)
        print(f"Accessible locations count: {accessible_locations.count()}", file=sys.stderr)
        for location in accessible_locations:
            print(f"  - Location: {location.name} (ID: {location.id}) - Business: {location.business.name}", file=sys.stderr)
    except ImportError as e:
        print(f"Import error: {e}", file=sys.stderr)
        accessible_locations = BusinessLocation.objects.none()
    except Exception as e:
        print(f"Error getting accessible locations: {e}", file=sys.stderr)
        accessible_locations = BusinessLocation.objects.none()
    
    # Redirection automatique si l'utilisateur a des permissions mais n'est pas propriétaire
    if not owned_businesses.exists() and accessible_locations.exists():
        first_location = accessible_locations.first()
        messages.info(request, _('Redirection automatique vers votre établissement accessible.'))
        return redirect('business:business_location_dashboard', pk=first_location.pk)
    
    print(f"=== FINAL DEBUG ===", file=sys.stderr)
    print(f"Context - owned_businesses: {owned_businesses.count()}", file=sys.stderr)
    print(f"Context - accessible_locations: {accessible_locations.count()}", file=sys.stderr)
    print("=" * 50, file=sys.stderr)
    
    context = {
        'owned_businesses': owned_businesses,
        'accessible_locations': accessible_locations,
        'has_permissions': accessible_locations.exists(),
        'title': _('Mes Entreprises'),
        'debug_info': {
            'user_id': request.user.id,
            'username': request.user.username,
            'owned_count': owned_businesses.count(),
            'accessible_count': accessible_locations.count(),
        }
    }
    return render(request, 'business/my_businesses.html', context)

@login_required
def debug_businesses(request):
    """
    Vue de debug pour vérifier les entreprises dans la base de données
    """
    import sys
    print("=" * 50, file=sys.stderr)
    print("=== DEBUG BUSINESSES ===", file=sys.stderr)
    
    # Toutes les entreprises
    all_businesses = Business.objects.all()
    print(f"Total businesses in DB: {all_businesses.count()}", file=sys.stderr)
    for business in all_businesses:
        print(f"  - Business: {business.name} (ID: {business.id}) - Owner: {business.owner.username if business.owner else 'None'}", file=sys.stderr)
    
    # Vos entreprises
    your_businesses = Business.objects.filter(owner=request.user)
    print(f"Your businesses: {your_businesses.count()}", file=sys.stderr)
    for business in your_businesses:
        print(f"  - Your Business: {business.name} (ID: {business.id})", file=sys.stderr)
    
    # Toutes les locations
    all_locations = BusinessLocation.objects.all()
    print(f"Total locations in DB: {all_locations.count()}", file=sys.stderr)
    for location in all_locations:
        print(f"  - Location: {location.name} (ID: {location.id}) - Business: {location.business.name if location.business else 'None'}", file=sys.stderr)
    
    print("=" * 50, file=sys.stderr)
    
    return JsonResponse({
        'total_businesses': all_businesses.count(),
        'your_businesses': your_businesses.count(),
        'total_locations': all_locations.count(),
        'user_id': request.user.id,
        'username': request.user.username,
    })

@login_required
def reset_wizard(request, business_pk):
    """
    Réinitialise le wizard et redirige vers l'étape 1
    """
    business = get_object_or_404(Business, pk=business_pk)
    
    # Check if user is the owner
    if business.owner != request.user:
        messages.error(request, _('You do not have permission to reset this wizard.'))
        return redirect('business:business_detail', pk=business.pk)
    
    # Nettoyer la session
    session_keys = ['wizard_location_data', 'wizard_hours_data', 'wizard_amenities_data', 'wizard_temp_images']
    for key in session_keys:
        if key in request.session:
            del request.session[key]
    
    messages.success(request, _('Le wizard a été réinitialisé. Vous pouvez recommencer.'))
    return redirect('business:location_wizard_create', business_pk=business_pk)

@login_required
@require_http_methods(["GET", "POST"])
def business_location_wizard(request, business_pk=None, pk=None):
    """
    Wizard multistep pour créer ou éditer un BusinessLocation avec horaires et commodités.
    """
    from apps.business.models.business_hours import BusinessHours
    
    def clean_wizard_session(request):
        """Nettoyer les données du wizard de la session"""
        keys_to_clean = [
            'wizard_location_data', 'wizard_hours_data', 
            'wizard_amenities_data', 'wizard_temp_images'
        ]
        for key in keys_to_clean:
            if key in request.session:
                del request.session[key]

    def clean_data_value(value):
        """Nettoyer une valeur de données en supprimant les espaces et caractères non-breaking"""
        if value is None:
            return None
        if isinstance(value, str):
            # Supprimer les espaces non-breaking et les espaces normaux
            cleaned = value.replace('\xa0', ' ').strip()
            # Retourner None si la chaîne est vide après nettoyage
            return cleaned if cleaned else None
        return value

    def debug_session_data(request, step_name):
        """Fonction de debug pour afficher les données de session"""
        print(f"=== DEBUG {step_name} ===")
        hours_data = request.session.get('wizard_hours_data', {})
        print(f"hours_data: {hours_data}")
        print(f"type hours_data: {type(hours_data)}")
        if hours_data:
            print(f"clés: {list(hours_data.keys())}")
            print(f"types des clés: {[type(k) for k in hours_data.keys()]}")
            for key, value in hours_data.items():
                print(f"  {key} ({type(key)}): {value}")
        print("=" * 50)
    
    def normalize_hours_data(hours_data):
        """Normalise les données d'horaires en convertissant les clés en entiers"""
        if not hours_data:
            return {}
        
        normalized = {}
        for key, value in hours_data.items():
            try:
                # Convertir la clé en entier
                int_key = int(key)
                normalized[int_key] = value
            except (ValueError, TypeError):
                # Si la conversion échoue, garder la clé originale
                normalized[key] = value
        
        return normalized
    
    def reset_wizard(request, business):
        """Réinitialise le wizard et redirige vers l'étape 1"""
        clean_wizard_session(request)
        messages.warning(request, _("Le wizard a été réinitialisé. Veuillez recommencer."))
        return redirect(f"{request.path}?step=1")
    
    is_edit = pk is not None
    step = int(request.GET.get('step', 1))
    max_step = 5
    location = None
    business = None
    errors = []

    # Validation de l'étape
    if step < 1 or step > max_step:
        step = 1

    if is_edit:
        location = get_object_or_404(BusinessLocation, pk=pk)
        business = location.business
        if location.business.owner != request.user:
            messages.error(request, _("Vous n'avez pas la permission d'éditer cet établissement."))
            return redirect('business:business_detail', pk=business.pk)
    else:
        business = get_object_or_404(Business, pk=business_pk)
        if business.owner != request.user:
            messages.error(request, _("Vous n'avez pas la permission d'ajouter une succursale à cette entreprise."))
            return redirect('business:business_detail', pk=business.pk)
        
        # Vérifier que les étapes précédentes sont complétées
        if step > 1 and not request.session.get('wizard_location_data'):
            return reset_wizard(request, business)
        if step > 2 and not request.session.get('wizard_hours_data'):
            return reset_wizard(request, business)
        if step > 3 and not request.session.get('wizard_amenities_data'):
            return reset_wizard(request, business)

    # ÉTAPE 1 : Infos de base et adresse
    if step == 1:
        if request.method == 'POST':
            # Collecte des données du formulaire
            data = request.POST
            name = clean_data_value(data.get('name', ''))
            business_location_type = clean_data_value(data.get('business_location_type', ''))
            phone = clean_data_value(data.get('phone', ''))
            email = clean_data_value(data.get('email', ''))
            registration_number = clean_data_value(data.get('registration_number', ''))
            description = clean_data_value(data.get('description', ''))
            founded_date = clean_data_value(data.get('founded_date', ''))
            
            # Champs d'adresse
            street_address = clean_data_value(data.get('street_address', ''))
            neighborhood = clean_data_value(data.get('neighborhood', ''))
            city = clean_data_value(data.get('city', ''))
            region = clean_data_value(data.get('region', ''))
            country = clean_data_value(data.get('country', '')) or 'Cameroon'
            postal_code = clean_data_value(data.get('postal_code', ''))
            latitude = clean_data_value(data.get('latitude', ''))
            longitude = clean_data_value(data.get('longitude', ''))

            # Validation minimale
            if not name:
                errors.append(_("Le nom est requis."))
            if not business_location_type:
                errors.append(_("Le type d'établissement est requis."))
            if not description:
                errors.append(_("La description est requise."))
            if not city:
                errors.append(_("La ville est requise."))

            # Validation des coordonnées si fournies
            if latitude and longitude:
                try:
                    lat = float(latitude)
                    lon = float(longitude)
                    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
                        errors.append(_("Les coordonnées géographiques sont invalides."))
                except ValueError:
                    errors.append(_("Les coordonnées géographiques doivent être des nombres."))

            # Si pas d'erreur, on stocke en session et passe à l'étape suivante
            if not errors:
                request.session['wizard_location_data'] = {
                    'name': name,
                    'business_location_type': business_location_type,
                    'phone': phone,
                    'email': email,
                    'registration_number': registration_number,
                    'description': description,
                    'founded_date': founded_date,
                    'street_address': street_address,
                    'neighborhood': neighborhood,
                    'city': city,
                    'region': region,
                    'country': country,
                    'postal_code': postal_code,
                    'latitude': latitude,
                    'longitude': longitude,
                }
                return redirect(f"{request.path}?step=2")
            # Sinon, on réaffiche le formulaire avec les erreurs
            location_data = request.session.get('wizard_location_data', {})
            location_data.update({
                'name': name,
                'business_location_type': business_location_type,
                'phone': phone,
                'email': email,
                'registration_number': registration_number,
                'description': description,
                'founded_date': founded_date,
                'street_address': street_address,
                'neighborhood': neighborhood,
                'city': city,
                'region': region,
                'country': country,
                'postal_code': postal_code,
                'latitude': latitude,
                'longitude': longitude,
            })
        else:
            location_data = request.session.get('wizard_location_data', {})
            if is_edit and location:
                location_data = {
                    'name': location.name,
                    'business_location_type': location.business_location_type,
                    'phone': location.phone,
                    'email': location.email,
                    'registration_number': location.registration_number,
                    'description': location.description,
                    'founded_date': location.founded_date.strftime('%Y-%m-%d') if location.founded_date else '',
                    'street_address': location.street_address,
                    'neighborhood': location.neighborhood,
                    'city': location.city,
                    'region': location.region,
                    'country': location.country,
                    'postal_code': location.postal_code,
                    'latitude': str(location.latitude) if location.latitude else '',
                    'longitude': str(location.longitude) if location.longitude else '',
                }
        # Injection dans le contexte
        context = {
            'step': step,
            'max_step': max_step,
            'is_edit': is_edit,
            'location': location_data,
            'business': business,
            'errors': errors,
            'BUSINESS_TYPES': BusinessLocation.BUSINESS_TYPES,
        }
        return render(request, 'business/business_location_wizard.html', context)

    # ÉTAPE 2 : Horaires
    if step == 2:
        if request.method == 'POST':
            # Collecte des horaires pour chaque jour
            hours_data = {}
            has_at_least_one_open_day = False
            
            for day, day_label in BusinessHours.DAYS_OF_WEEK:
                is_open = request.POST.get(f'is_open_{day}', '') == 'on'
                opening_time = request.POST.get(f'opening_time_{day}', '').strip()
                closing_time = request.POST.get(f'closing_time_{day}', '').strip()
                break_start = request.POST.get(f'break_start_{day}', '').strip()
                break_end = request.POST.get(f'break_end_{day}', '').strip()
                is_closed = not is_open
                
                if is_open:
                    has_at_least_one_open_day = True
                
                # Validation minimale
                if is_open:
                    if not opening_time or not closing_time:
                        errors.append(_(f"Heures d'ouverture et de fermeture requises pour {day_label}."))
                    elif closing_time <= opening_time:
                        errors.append(_(f"L'heure de fermeture doit être après l'heure d'ouverture pour {day_label}."))
                    else:
                        # Validation des pauses seulement si les heures principales sont valides
                        if (break_start and not break_end) or (break_end and not break_start):
                            errors.append(_(f"Pause incomplète pour {day_label}. Veuillez spécifier le début et la fin."))
                        elif break_start and break_end:
                            if break_end <= break_start:
                                errors.append(_(f"La fin de pause doit être après le début pour {day_label}."))
                            elif break_start < opening_time:
                                errors.append(_(f"Le début de pause ne peut pas être avant l'ouverture pour {day_label}."))
                            elif break_end > closing_time:
                                errors.append(_(f"La fin de pause ne peut pas être après la fermeture pour {day_label}."))
                
                hours_data[day] = {
                    'is_closed': is_closed,
                    'opening_time': opening_time,
                    'closing_time': closing_time,
                    'break_start': break_start,
                    'break_end': break_end,
                }
            
            # Validation supplémentaire : au moins un jour ouvert
            if not has_at_least_one_open_day:
                errors.append(_("Veuillez sélectionner au moins un jour d'ouverture."))
            
            if not errors:
                print("=== DEBUG ÉTAPE 2 - AVANT SAUVEGARDE ===")
                print("hours_data à sauvegarder:", hours_data)
                print("Type de hours_data:", type(hours_data))
                print("Clés dans hours_data:", list(hours_data.keys()))
                print("Types des clés:", [type(k) for k in hours_data.keys()])
                request.session['wizard_hours_data'] = hours_data
                print("=== DEBUG ÉTAPE 2 - APRÈS SAUVEGARDE ===")
                print("Session après sauvegarde:", request.session.get('wizard_hours_data', {}))
                debug_session_data(request, "ÉTAPE 2 - APRÈS SAUVEGARDE")
                return redirect(f"{request.path}?step=3")
            # Si erreurs, on garde les données pour réaffichage
        else:
            debug_session_data(request, "ÉTAPE 2 - RÉCUPÉRATION")
            hours_data = request.session.get('wizard_hours_data', {})
            print("=== DEBUG ÉTAPE 2 - AVANT NORMALISATION ===")
            print("hours_data brut:", hours_data)
            print("Type de hours_data brut:", type(hours_data))
            if hours_data:
                print("Clés dans hours_data brut:", list(hours_data.keys()))
                print("Types des clés brut:", [type(k) for k in hours_data.keys()])
            hours_data = normalize_hours_data(hours_data)
            print("=== DEBUG ÉTAPE 2 - APRÈS NORMALISATION ===")
            print("hours_data normalisé:", hours_data)
            print("Type de hours_data normalisé:", type(hours_data))
            if hours_data:
                print("Clés dans hours_data normalisé:", list(hours_data.keys()))
                print("Types des clés normalisé:", [type(k) for k in hours_data.keys()])
            print("Heures de la session :", hours_data)
            if is_edit and location:
                hours_data = {}
                for h in location.business_hours.all():
                    hours_data[h.day] = {
                        'is_closed': h.is_closed,
                        'opening_time': h.opening_time.strftime('%H:%M') if h.opening_time else '',
                        'closing_time': h.closing_time.strftime('%H:%M') if h.closing_time else '',
                        'break_start': h.break_start.strftime('%H:%M') if h.break_start else '',
                        'break_end': h.break_end.strftime('%H:%M') if h.break_end else '',
                    }
        context = {
            'step': step,
            'max_step': max_step,
            'is_edit': is_edit,
            'location': location,
            'business': business,
            'business_hours_model': BusinessHours,
            'hours_data': hours_data,
            'errors': errors,
        }
        return render(request, 'business/business_location_wizard.html', context)

    # ÉTAPE 3 : Commodités
    if step == 3:
        amenity_categories = BusinessAmenityCategory.objects.prefetch_related('amenities').filter(is_active=True)
        if request.method == 'POST':
            selected_amenities = []
            details_dict = {}
            for cat in amenity_categories:
                for amenity in cat.amenities.all():
                    if request.POST.get(f'amenity_{amenity.id}', '') == 'on':
                        selected_amenities.append(amenity.id)
                        details_dict[amenity.id] = request.POST.get(f'details_{amenity.id}', '').strip()
            if not selected_amenities:
                errors.append(_("Veuillez sélectionner au moins une commodité."))
            if not errors:
                request.session['wizard_amenities_data'] = {
                    'selected_amenities': selected_amenities,
                    'details_dict': details_dict,
                }
                return redirect(f"{request.path}?step=4")
        else:
            amenities_data = request.session.get('wizard_amenities_data', {})
            selected_amenities = amenities_data.get('selected_amenities', [])
            details_dict = amenities_data.get('details_dict', {})
            if is_edit and location:
                selected_amenities = [a.amenity.id for a in location.amenity_assignments.all()]
                details_dict = {a.amenity.id: a.details for a in location.amenity_assignments.all()}
        
        # Créer un objet factice pour les commodités
        class DummyLocation:
            def __init__(self, selected, details):
                self._selected = selected
                self._details = details
                self.amenity_assignments = DummyAssignments(selected, details)
        
        class DummyAssignments:
            def __init__(self, selected, details):
                self._selected = selected
                self._details = details
            def all(self):
                return [type('A', (), {'amenity': type('B', (), {'id': i})(), 'details': self._details.get(i, '')}) for i in self._selected]
        
        dummy_location = DummyLocation(selected_amenities, details_dict)
        
        context = {
            'step': step,
            'max_step': max_step,
            'is_edit': is_edit,
            'location': location or dummy_location,
            'business': business,
            'amenity_categories': amenity_categories,
            'errors': errors,
        }
        return render(request, 'business/business_location_wizard.html', context)

    # ÉTAPE 4 : Résumé et validation finale
    if step == 4:
        location_data = request.session.get('wizard_location_data', {})
        hours_data = request.session.get('wizard_hours_data', {})
        hours_data = normalize_hours_data(hours_data)  # Normaliser les clés
        amenities_data = request.session.get('wizard_amenities_data', {})
        amenity_categories = BusinessAmenityCategory.objects.prefetch_related('amenities').filter(is_active=True)
        
        # Debug: afficher les données des horaires
        debug_session_data(request, "ÉTAPE 4 - RÉCUPÉRATION")
        print("=== DEBUG ÉTAPE 4 ===")
        print("hours_data:", hours_data)
        print("type hours_data:", type(hours_data))
        
        # Construction des objets pour affichage
        class DummyAssignment:
            def __init__(self, amenity, details):
                self.amenity = amenity
                self.details = details
        
        # Classe DummyHours définie en dehors de la boucle
        class DummyHours:
            def __init__(self, day, label, h):
                self.day = day
                self.get_day_display = lambda: label
                self.is_closed = h.get('is_closed', True)
                self.opening_time = h.get('opening_time', '')
                self.closing_time = h.get('closing_time', '')
                self.break_start = h.get('break_start', '')
                self.break_end = h.get('break_end', '')
        
        amenity_assignments = []
        for cat in amenity_categories:
            for amenity in cat.amenities.all():
                if str(amenity.id) in [str(i) for i in amenities_data.get('selected_amenities', [])]:
                    details = amenities_data.get('details_dict', {}).get(amenity.id, '')
                    amenity_assignments.append(DummyAssignment(amenity, details))
        
        # Construction des horaires pour affichage
        business_hours = []
        print("=== CONSTRUCTION BUSINESS_HOURS ===")
        print("BusinessHours.DAYS_OF_WEEK:", BusinessHours.DAYS_OF_WEEK)
        for day, day_label in BusinessHours.DAYS_OF_WEEK:
            print(f"Traitement jour {day} ({day_label})")
            h = hours_data.get(day, {})
            print(f"  Données trouvées: {h}")
            print(f"  Type de day: {type(day)}")
            print(f"  Clés disponibles dans hours_data: {list(hours_data.keys())}")
            dummy_hours = DummyHours(day, day_label, h)
            business_hours.append(dummy_hours)
            print(f"  Objet créé: {dummy_hours.get_day_display()} - ouvert={not dummy_hours.is_closed}")
        
        print("business_hours construit:", len(business_hours), "éléments")
        for h in business_hours:
            print(f"  - {h.get_day_display()}: ouvert={not h.is_closed}, {h.opening_time}-{h.closing_time}")
        
        # Créer un objet factice pour la location avec toutes les données
        class DummyLocationSummary:
            def __init__(self, location_data, amenity_assignments):
                self.amenity_assignments = amenity_assignments
                # Ajouter tous les champs de location_data comme attributs
                for key, value in location_data.items():
                    setattr(self, key, value)
                # Méthodes spéciales pour l'affichage
                def get_business_location_type_display(self):
                    business_types = dict(BusinessLocation.BUSINESS_TYPES)
                    return business_types.get(self.business_location_type, self.business_location_type)
                setattr(self, 'get_business_location_type_display', get_business_location_type_display.__get__(self))
        
        dummy_location = DummyLocationSummary(location_data, amenity_assignments)
        
        # Validation finale et création/sauvegarde
        if request.method == 'POST':
            # Au lieu de créer la location ici, on redirige vers l'étape 5
            return redirect(f"{request.path}?step=5")
        
        context = {
            'step': step,
            'max_step': max_step,
            'is_edit': is_edit,
            'location': location or dummy_location,
            'business': business,
            'business_hours': business_hours,
            'amenity_assignments': amenity_assignments,
            'errors': errors,
            'debug': True,  # Activer le debug
        }
        return render(request, 'business/business_location_wizard.html', context)

    # ÉTAPE 5 : Images (nouvelle étape)
    if step == 5:
        if request.method == 'POST':
            # Récupérer toutes les données du wizard
            location_data = request.session.get('wizard_location_data', {})
            hours_data = request.session.get('wizard_hours_data', {})
            amenities_data = request.session.get('wizard_amenities_data', {})
            temp_ids = request.session.get('wizard_temp_images', [])
            primary_image_id = request.POST.get('is_primary')

            # Création ou update du BusinessLocation
            if is_edit:
                loc = location
            else:
                loc = BusinessLocation(business=business, owner=request.user)

            print("=== DEBUG ÉTAPE 5 - AVANT SAUVEGARDE ===")
            print("location_data:", location_data.items())
            
            # Mise à jour des champs de base
            for k, v in location_data.items():
                # Nettoyer la valeur avant traitement
                cleaned_value = clean_data_value(v)
                
                if k in ['latitude', 'longitude'] and cleaned_value:
                    try:
                        setattr(loc, k, float(cleaned_value))
                    except ValueError:
                        setattr(loc, k, None)
                elif k == 'founded_date' and cleaned_value:
                    try:
                        from datetime import datetime
                        setattr(loc, k, datetime.strptime(cleaned_value, '%Y-%m-%d').date())
                    except ValueError:
                        setattr(loc, k, None)
                else:
                    setattr(loc, k, cleaned_value)
            
            loc.save()
            
            # Horaires
            loc.business_hours.all().delete()
            for day, h in hours_data.items():
                BusinessHours.objects.create(
                    business_location=loc,
                    day=day,
                    is_closed=h.get('is_closed', True),
                    opening_time=h.get('opening_time') or None,
                    closing_time=h.get('closing_time') or None,
                    break_start=h.get('break_start') or None,
                    break_end=h.get('break_end') or None,
                )
            
            # Commodités
            loc.amenity_assignments.all().delete()
            amenity_categories = BusinessAmenityCategory.objects.prefetch_related('amenities').filter(is_active=True)
            for cat in amenity_categories:
                for amenity in cat.amenities.all():
                    if str(amenity.id) in [str(i) for i in amenities_data.get('selected_amenities', [])]:
                        details = amenities_data.get('details_dict', {}).get(amenity.id, '')
                        BusinessAmenityAssignment.objects.create(
                            business_location=loc,
                            amenity=amenity,
                            details=details,
                            is_active=True
                        )
            
            # Associer les images temporaires à la location
            if temp_ids:
                images = BusinessLocationImage.objects.filter(id__in=temp_ids, business_location=None)
                for img in images:
                    img.business_location = loc
                    img.is_primary = (str(img.id) == primary_image_id)
                    img.save()
            
            # Nettoyage session
            clean_wizard_session(request)
            
            messages.success(request, _("Établissement créé avec succès avec ses images. Il sera vérifié par l'administrateur."))
            return redirect('business:location_detail', pk=loc.pk)
        
        context = {
            'step': step,
            'max_step': max_step,
            'is_edit': is_edit,
            'location': location,
            'business': business,
            'errors': errors,
        }
        return render(request, 'business/business_location_wizard.html', context)

@csrf_exempt
@login_required
def upload_image_temp(request):
    if request.method != 'POST' or 'image' not in request.FILES:
        return JsonResponse({'success': False, 'error': 'Méthode invalide ou fichier manquant.'})
    image = request.FILES['image']
    # Créer une instance temporaire (business_location=None)
    temp_img = BusinessLocationImage.objects.create(
        business_location=None,
        image=image,
        is_primary=False
    )
    # Stocker l'ID dans la session
    temp_ids = request.session.get('wizard_temp_images', [])
    temp_ids.append(temp_img.id)
    request.session['wizard_temp_images'] = temp_ids
    return JsonResponse({'success': True, 'id': temp_img.id, 'url': temp_img.image.url})

@csrf_exempt
@login_required
def delete_image_temp(request, image_id):
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Méthode invalide.'})
    temp_ids = request.session.get('wizard_temp_images', [])
    if image_id in temp_ids:
        try:
            img = BusinessLocationImage.objects.get(id=image_id, business_location=None)
            img.image.delete(save=False)
            img.delete()
            temp_ids.remove(image_id)
            request.session['wizard_temp_images'] = temp_ids
            return JsonResponse({'success': True})
        except BusinessLocationImage.DoesNotExist:
            pass
    return JsonResponse({'success': False, 'error': 'Image non trouvée.'})

@login_required
def list_image_temp(request):
    temp_ids = request.session.get('wizard_temp_images', [])
    images = BusinessLocationImage.objects.filter(id__in=temp_ids, business_location=None)
    data = [
        {
            'id': img.id,
            'url': img.image.url,
            'is_primary': False  # Le choix principal est géré côté JS avant validation finale
        }
        for img in images
    ]
    return JsonResponse({'images': data})


@login_required
def business_location_dashboard(request, pk):
    """
    Dashboard pour gérer une business location spécifique.
    Affiche des informations et actions adaptées au type de business.
    """
    location = get_object_or_404(BusinessLocation, pk=pk)
    
    from .permissions import has_any_permission, log_user_action
    if not (location.business.owner == request.user or has_any_permission(request.user, location)):
        messages.error(request, _("Vous n'avez pas les permissions pour accéder à ce dashboard."))
        return redirect('business:business_detail', pk=location.business.pk)
    
    log_user_action(
        user=request.user,
        location=location,
        action_type='dashboard_access',
        description=f'Accès au dashboard de {location.name}',
        request=request
    )
    
    context = {
        'location': location,
        'business': location.business,
    }
    
    today = date.today()
    
    if location.business_location_type == 'restaurant':
        from apps.orders.models.menu_item import MenuItem
        from apps.orders.models.order import RestaurantOrder, OrderItem
        from apps.orders.forms import CustomRestaurantOrderForm, OrderCustomerForm
        menu_items = MenuItem.objects.filter(business_location=location)
        menu_items_in_stock = menu_items.filter(is_available=True, stock_quantity__gt=0)
        if request.method == 'POST':
            print("=== DEBUG: POST request received ===")
            print("POST data:", dict(request.POST))
            print("POST keys:", list(request.POST.keys()))
            print("menu_items:", request.POST.getlist('menu_items'))
            order_form = CustomRestaurantOrderForm(request.POST, business_location=location)
            customer_form = OrderCustomerForm(request.POST)
            print("=== DEBUG: Form validation ===")
            print("Order form valid:", order_form.is_valid())
            print("Customer form valid:", customer_form.is_valid())
            if not order_form.is_valid():
                print("Order form errors:", order_form.errors)
            if not customer_form.is_valid():
                print("Customer form errors:", customer_form.errors)
            if order_form.is_valid() and customer_form.is_valid():
                try:
                    print("=== DEBUG: Starting order creation ===")
                    # Recherche ou création du client
                    email = customer_form.cleaned_data['email']
                    phone = customer_form.cleaned_data['phone_number']
                    print(f"Customer email: {email}, phone: {phone}")
                    user_qs = User.objects.filter(email=email)
                    if not user_qs.exists() and phone:
                        user_qs = User.objects.filter(phone_number=phone)
                    if user_qs.exists():
                        customer = user_qs.first()
                    else:
                        customer = User.objects.create(
                            first_name=customer_form.cleaned_data['first_name'],
                            last_name=customer_form.cleaned_data['last_name'],
                            email=email,
                            phone_number=phone,
                            username=email or phone or f'user_{User.objects.count()+1}'
                        )
                    # Créer la commande principale
                    print("=== DEBUG: Creating main order ===")
                    order = order_form.save(commit=False)
                    order.customer = customer
                    order.business_location = location
                    order.status = 'READY'
                    order.payment_status = 'PAID'
                    order.payment_method = 'CASH'
                    
                    # Générer l'order_number
                    from django.utils.crypto import get_random_string
                    while True:
                        order_number = f"ORD{get_random_string(8).upper()}"
                        if not RestaurantOrder.objects.filter(order_number=order_number).exists():
                            break
                    order.order_number = order_number
                    
                    print(f"Order before save: customer={order.customer}, location={order.business_location}, order_number={order.order_number}")
                    # Calcule le sous-total avant de sauvegarder la commande
                    order.subtotal = sum(
                        menu_items_in_stock.get(id=item_id).price * int(request.POST.get(f'quantity_{item_id}', 1))
                        for item_id in request.POST.getlist('menu_items')
                    )
                    # Calcule le total_amount avant de sauvegarder la commande
                    try:
                        order.calculate_total()
                    except Exception:
                        # Si la méthode n'existe pas, calcule manuellement
                        order.total_amount = order.subtotal
                    order.save()

                    # Crée la transaction espèces automatiquement
                    from apps.wallets.services.wallet_service import WalletService
                    wallet, _ = WalletService.get_or_create_business_wallet(location.business)
                    from django.utils.crypto import get_random_string
                    reference = get_random_string(16)
                    UserTransaction.objects.create(
                        wallet_content_type=ContentType.objects.get_for_model(wallet),
                        wallet_object_id=wallet.id,
                        content_type=ContentType.objects.get_for_model(order),
                        object_id=order.id,
                        transaction_type='CASH_PAYMENT',
                        amount=order.total_amount,
                        status='COMPLETED',
                        reference=reference,
                        description=f'Paiement espèces pour commande {order.order_number}'
                    )

                    print(f"Order created with ID: {order.id}")
                    # Créer les OrderItem à partir des plats sélectionnés
                    print("=== DEBUG: Creating order items ===")
                    menu_item_ids = request.POST.getlist('menu_items')
                    print(f"Menu item IDs: {menu_item_ids}")
                    for item_id in menu_item_ids:
                        try:
                            menu_item = menu_items_in_stock.get(id=item_id)
                            quantity = int(request.POST.get(f'quantity_{item_id}', 1))
                            if quantity > 0 and quantity <= menu_item.stock_quantity:
                                OrderItem.objects.create(
                                    restaurant_order=order,
                                    menu_item=menu_item,
                                    quantity=quantity,
                                    unit_price=menu_item.price,
                                    total_price=menu_item.price * quantity
                                )
                                menu_item.stock_quantity -= quantity
                                if menu_item.stock_quantity == 0:
                                    menu_item.is_available = False
                                menu_item.save()
                        except MenuItem.DoesNotExist:
                            continue
                    order.calculate_total()
                    order.save()
                    print(f"=== DEBUG: Order completed successfully ===")
                    print(f"Order total: {order.total_amount}")
                    print(f"Order items count: {order.items.count()}")
                    messages.success(request, _('Order created successfully.'))
                    return redirect(f"{reverse('orders:order_list')}?location={location.pk}")
                except Exception as e:
                    messages.error(request, str(e))
            else:
                # Formulaires invalides, on les repasse au contexte
                print("=== DEBUG: Form validation failed ===")
                print("Order form errors:", order_form.errors)
                print("Customer form errors:", customer_form.errors)
                # Les formulaires avec erreurs sont repassés au contexte automatiquement
        else:
            order_form = CustomRestaurantOrderForm(business_location=location)
            customer_form = OrderCustomerForm()
        context.update({
            'menu_items': menu_items,
            'menu_items_in_stock': menu_items_in_stock,
            'order_form': order_form,
            'customer_form': customer_form,
            'business_location': location,
            'recent_orders': RestaurantOrder.objects.filter(business_location=location).order_by('-created_at')[:5],
            'total_menu_items': menu_items.count(),
            'total_orders': RestaurantOrder.objects.filter(business_location=location).count(),
        })
        # Ajout du solde réel du wallet business
        from apps.wallets.services.wallet_service import WalletService
        wallet, _ = WalletService.get_or_create_business_wallet(location.business)
        context['wallet_balance'] = wallet.balance
        template_name = 'business/dashboard/restaurant_dashboard.html'
        # Nouvelle logique pour tous les types de business location
        def get_wallet_cash_totals(bookings_today):
            total_wallet = 0
            total_cash = 0
            total_day = 0
            for booking in bookings_today:
                booking_ct = ContentType.objects.get_for_model(booking)
                wallet_amount = UserTransaction.objects.filter(
                    content_type=booking_ct,
                    object_id=booking.pk,
                    transaction_type='PAYMENT',
                    status='COMPLETED'
                ).aggregate(total=Sum('amount'))['total'] or 0
                cash_amount = UserTransaction.objects.filter(
                    content_type=booking_ct,
                    object_id=booking.pk,
                    transaction_type='CASH_PAYMENT',
                    status='COMPLETED'
                ).aggregate(total=Sum('amount'))['total'] or 0
                total_wallet += wallet_amount
                total_cash += cash_amount
                total_day += wallet_amount + cash_amount
            return total_wallet, total_cash, total_day
        orders_today = RestaurantOrder.objects.filter(
            business_location=location,
            payment_status='PAID',
            created_at__date=today
        )
        total_wallet, total_cash, total_day = get_wallet_cash_totals(orders_today)
        context.update({
            'total_day': total_day,
            'total_wallet': total_wallet,
            'total_cash': total_cash,
            'solde_wallet': total_wallet,
            'booking_transactions_wallet': orders_today.filter(payment_method='WALLET').order_by('-created_at')[:5],
            'booking_transactions_cash': orders_today.filter(payment_method='CASH').order_by('-created_at')[:5],
        })
    elif location.business_location_type == 'hotel':
        from apps.rooms.models import Room, RoomBooking
        rooms = Room.objects.filter(business_location=location)
        recent_bookings = RoomBooking.objects.filter(room__business_location=location).order_by('-created_at')[:5]
        context.update({
            'rooms': rooms,
            'recent_bookings': recent_bookings,
            'total_rooms': rooms.count(),
            'total_bookings': RoomBooking.objects.filter(room__business_location=location).count(),
        })
        template_name = 'business/dashboard/hotel_dashboard.html'
        # Nouvelle logique pour tous les types de business location
        def get_wallet_cash_totals(bookings_today):
            total_wallet = 0
            total_cash = 0
            total_day = 0
            for booking in bookings_today:
                booking_ct = ContentType.objects.get_for_model(booking)
                wallet_amount = UserTransaction.objects.filter(
                    content_type=booking_ct,
                    object_id=booking.pk,
                    transaction_type='PAYMENT',
                    status='COMPLETED'
                ).aggregate(total=Sum('amount'))['total'] or 0
                cash_amount = UserTransaction.objects.filter(
                    content_type=booking_ct,
                    object_id=booking.pk,
                    transaction_type='CASH_PAYMENT',
                    status='COMPLETED'
                ).aggregate(total=Sum('amount'))['total'] or 0
                print(wallet_amount, cash_amount)
                total_wallet += wallet_amount
                total_cash += cash_amount
                total_day += wallet_amount + cash_amount
            return total_wallet, total_cash, total_day
        bookings_today = RoomBooking.objects.filter(room__business_location=location, created_at__date=today)
        total_wallet, total_cash, total_day = get_wallet_cash_totals(bookings_today)
        
        # Préparer les listes de transactions wallet et cash pour l'affichage
        booking_transactions_wallet = []
        booking_transactions_cash = []
        for booking in bookings_today:
            booking_ct = ContentType.objects.get_for_model(booking)
            wallet_transactions = UserTransaction.objects.filter(
                content_type=booking_ct,
                object_id=booking.pk,
                transaction_type='PAYMENT',
                status='COMPLETED'
            ).order_by('-created_at')[:5]
            cash_transactions = UserTransaction.objects.filter(
                content_type=booking_ct,
                object_id=booking.pk,
                transaction_type='CASH_PAYMENT',
                status='COMPLETED'
            ).order_by('-created_at')[:5]
            booking_transactions_wallet.extend(wallet_transactions)
            booking_transactions_cash.extend(cash_transactions)
        
        context.update({
            'total_day': total_day,
            'total_wallet': total_wallet,
            'total_cash': total_cash,
            'solde_wallet': total_wallet,
            'booking_transactions_wallet': booking_transactions_wallet,
            'booking_transactions_cash': booking_transactions_cash,
        })
    elif location.business_location_type == 'transport':
        from apps.vehicles.models import Vehicle, VehicleBooking
        vehicles = Vehicle.objects.filter(business_location=location)
        recent_bookings = VehicleBooking.objects.filter(vehicle__business_location=location).order_by('-created_at')[:5]
        context.update({
            'vehicles': vehicles,
            'recent_bookings': recent_bookings,
            'total_vehicles': vehicles.count(),
            'total_bookings': VehicleBooking.objects.filter(vehicle__business_location=location).count(),
        })
        template_name = 'business/dashboard/vehicle_dashboard.html'
        # Nouvelle logique pour tous les types de business location
        def get_wallet_cash_totals(bookings_today):
            total_wallet = 0
            total_cash = 0
            total_day = 0
            for booking in bookings_today:
                booking_ct = ContentType.objects.get_for_model(booking)
                wallet_amount = UserTransaction.objects.filter(
                    content_type=booking_ct,
                    object_id=booking.pk,
                    transaction_type='PAYMENT',
                    status='COMPLETED'
                ).aggregate(total=Sum('amount'))['total'] or 0
                cash_amount = UserTransaction.objects.filter(
                    content_type=booking_ct,
                    object_id=booking.pk,
                    transaction_type='CASH_PAYMENT',
                    status='COMPLETED'
                ).aggregate(total=Sum('amount'))['total'] or 0
                total_wallet += wallet_amount
                total_cash += cash_amount
                total_day += wallet_amount + cash_amount
            return total_wallet, total_cash, total_day
        bookings_today = VehicleBooking.objects.filter(vehicle__business_location=location, created_at__date=today)
        total_wallet, total_cash, total_day = get_wallet_cash_totals(bookings_today)
        
        # Préparer les listes de transactions wallet et cash pour l'affichage
        booking_transactions_wallet = []
        booking_transactions_cash = []
        for booking in bookings_today:
            booking_ct = ContentType.objects.get_for_model(booking)
            wallet_transactions = UserTransaction.objects.filter(
                content_type=booking_ct,
                object_id=booking.pk,
                transaction_type='PAYMENT',
                status='COMPLETED'
            ).order_by('-created_at')[:5]
            cash_transactions = UserTransaction.objects.filter(
                content_type=booking_ct,
                object_id=booking.pk,
                transaction_type='CASH_PAYMENT',
                status='COMPLETED'
            ).order_by('-created_at')[:5]
            booking_transactions_wallet.extend(wallet_transactions)
            booking_transactions_cash.extend(cash_transactions)
        
        context.update({
            'total_day': total_day,
            'total_wallet': total_wallet,
            'total_cash': total_cash,
            'solde_wallet': total_wallet,
            'booking_transactions_wallet': booking_transactions_wallet,
            'booking_transactions_cash': booking_transactions_cash,
        })
    elif location.business_location_type == 'tour_operator':
        from apps.tours.models import Tour, TourDestination, TourBooking, TourReview, TourSchedule
        today = date.today()
        # TOURS
        tours = Tour.objects.filter(business_location=location).prefetch_related('destinations', 'tour_schedules')
        total_tours = tours.count()
        # DESTINATIONS
        destinations = TourDestination.objects.filter(tour__business_location=location, is_active=True).select_related('tour')
        # SCHEDULES
        schedules = TourSchedule.objects.filter(tour__business_location=location).select_related('tour')
        # BOOKINGS (réservations du jour)
        bookings_today = TourBooking.objects.filter(
            tour_schedule__tour__business_location=location,
            created_at__date=today
        ).select_related('customer', 'tour_schedule__tour')
        # RÉSERVATIONS RÉCENTES
        recent_bookings = TourBooking.objects.filter(
            tour_schedule__tour__business_location=location
        ).order_by('-created_at')[:5]
        # REVIEWS
        reviews = TourReview.objects.filter(tour__business_location=location).select_related('tour', 'reviewer')
        # Synthèse financière du jour (transactions liées aux bookings)
        def get_wallet_cash_totals(bookings):
            total_wallet = 0
            total_cash = 0
            booking_transactions_wallet = []
            booking_transactions_cash = []
            for booking in bookings:
                booking_ct = ContentType.objects.get_for_model(booking)
                wallet_transactions = UserTransaction.objects.filter(
                    content_type=booking_ct,
                    object_id=booking.pk,
                    transaction_type='PAYMENT',
                    status='COMPLETED'
                )
                cash_transactions = UserTransaction.objects.filter(
                    content_type=booking_ct,
                    object_id=booking.pk,
                    transaction_type='CASH_PAYMENT',
                    status='COMPLETED'
                )
                total_wallet += wallet_transactions.aggregate(total=Sum('amount'))['total'] or 0
                total_cash += cash_transactions.aggregate(total=Sum('amount'))['total'] or 0
                booking_transactions_wallet.extend(wallet_transactions)
                booking_transactions_cash.extend(cash_transactions)
            return total_wallet, total_cash, booking_transactions_wallet, booking_transactions_cash
        total_wallet, total_cash, booking_transactions_wallet, booking_transactions_cash = get_wallet_cash_totals(bookings_today)
        total_day = total_wallet + total_cash
        # Synthèse financière du business location (transactions reçues par le wallet business)
        wallet = getattr(location, 'wallet', None)
        business_wallet_balance = wallet.balance if wallet else 0
        business_wallet_transactions_today = []
        business_cash_transactions_today = []
        business_total_wallet_today = 0
        business_total_cash_today = 0
        if wallet:
            wallet_ct = ContentType.objects.get_for_model(wallet)
            business_wallet_transactions_today = UserTransaction.objects.filter(
                wallet_content_type=wallet_ct,
                wallet_object_id=wallet.id,
                transaction_type='PAYMENT',
                status='COMPLETED',
                created_at__date=today
            ).order_by('-created_at')
            business_cash_transactions_today = UserTransaction.objects.filter(
                wallet_content_type=wallet_ct,
                wallet_object_id=wallet.id,
                transaction_type='CASH_PAYMENT',
                status='COMPLETED',
                created_at__date=today
            ).order_by('-created_at')
            business_total_wallet_today = sum(t.amount for t in business_wallet_transactions_today)
            business_total_cash_today = sum(t.amount for t in business_cash_transactions_today)
        # Détail des transactions du jour (pour tableau)
        orders_detail = bookings_today
        context.update({
            'tours': tours,
            'total_tours': total_tours,
            'destinations': destinations,
            'schedules': schedules,
            'recent_bookings': recent_bookings,
            'reviews': reviews,
            'orders_detail': orders_detail,
            'total_day': total_day,
            'total_wallet': total_wallet,
            'total_cash': total_cash,
            'booking_transactions_wallet': booking_transactions_wallet,
            'booking_transactions_cash': booking_transactions_cash,
            'business_wallet_balance': business_wallet_balance,
            'business_total_wallet_today': business_total_wallet_today,
            'business_total_cash_today': business_total_cash_today,
            'business_total_today': business_total_wallet_today + business_total_cash_today,
            'business_wallet_transactions_today': business_wallet_transactions_today,
            'business_cash_transactions_today': business_cash_transactions_today,
        })
        template_name = 'business/dashboard/tour_dashboard.html'
    else:
        template_name = 'business/dashboard/generic_dashboard.html'
    
    # Calculer les totaux du wallet du business location (transactions reçues par l'établissement)
    wallet = getattr(location, 'wallet', None)
    business_wallet_balance = wallet.balance if wallet else 0
    
    # Transactions reçues par le business location aujourd'hui
    business_wallet_transactions_today = []
    business_cash_transactions_today = []
    business_total_wallet_today = 0
    business_total_cash_today = 0
    
    if wallet:
        wallet_ct = ContentType.objects.get_for_model(wallet)
        
        # Transactions PAYMENT reçues par le business location (paiements wallet des clients)
        business_wallet_transactions_today = UserTransaction.objects.filter(
            wallet_content_type=wallet_ct,
            wallet_object_id=wallet.id,
            transaction_type='PAYMENT',
            status='COMPLETED',
            created_at__date=today
        ).order_by('-created_at')[:5]
        
        # Transactions CASH_PAYMENT reçues par le business location (paiements espèces des clients)
        business_cash_transactions_today = UserTransaction.objects.filter(
            wallet_content_type=wallet_ct,
            wallet_object_id=wallet.id,
            transaction_type='CASH_PAYMENT',
            status='COMPLETED',
            created_at__date=today
        ).order_by('-created_at')[:5]
        
        # Calculer les totaux du jour pour le business location
        business_total_wallet_today = sum(t.amount for t in business_wallet_transactions_today)
        business_total_cash_today = sum(t.amount for t in business_cash_transactions_today)
    
    # Ajouter les informations du wallet du business location au contexte
    context.update({
        'business_wallet_balance': business_wallet_balance,
        'business_total_wallet_today': business_total_wallet_today,
        'business_total_cash_today': business_total_cash_today,
        'business_total_today': business_total_wallet_today + business_total_cash_today,
        'business_wallet_transactions_today': business_wallet_transactions_today,
        'business_cash_transactions_today': business_cash_transactions_today,
    })
    
    # Transactions du jour pour le wallet de la business location (avec nom du client)
    transactions_wallet = []
    transactions_cash = []
    if wallet:
        wallet_ct = ContentType.objects.get_for_model(wallet)
        today = timezone.now().date()
        # Paiements wallet
        for t in UserTransaction.objects.filter(
            wallet_content_type=wallet_ct,
            wallet_object_id=wallet.id,
            transaction_type='PAYMENT',
            status='COMPLETED',
            created_at__date=today
        ).order_by('-created_at'):
            client = 'Non renseigné'
            client_obj = None
            phone = 'Non renseigné'
            order_number = 'Aucune commande'
            order_obj = None
            order_details = None
            if hasattr(t, 'content_object') and t.content_object:
                order = t.content_object
                order_obj = order
                if hasattr(order, 'customer') and order.customer:
                    client_obj = order.customer
                    if hasattr(client_obj, 'get_full_name'):
                        client = client_obj.get_full_name() or getattr(client_obj, 'username', 'Non renseigné')
                    else:
                        client = str(client_obj)
                    phone = getattr(client_obj, 'phone_number', '') or 'Non renseigné'
                order_number = getattr(order, 'order_number', '') or 'Aucune commande'
                # Préparer les détails de la commande
                order_details = {
                    'order_number': getattr(order, 'order_number', ''),
                    'order_type': getattr(order, 'order_type', ''),
                    'status': getattr(order, 'status', ''),
                    'payment_status': getattr(order, 'payment_status', ''),
                    'total_amount': getattr(order, 'total_amount', ''),
                    'created_at': getattr(order, 'created_at', None),
                    'customer': client,
                    'customer_phone': phone,
                    'items': [
                        {
                            'name': getattr(item.menu_item, 'name', ''),
                            'quantity': item.quantity,
                            'unit_price': item.unit_price,
                            'total_price': item.total_price
                        } for item in (order.items.all() if hasattr(order, 'items') and hasattr(order.items, 'all') else [])
                    ]
                }
            # Log pour debug
            if client_obj is not None:
                print(f"[DEBUG] client_obj type: {type(client_obj)} - value: {client_obj}")
            if order_obj is not None:
                print(f"[DEBUG] order_obj type: {type(order_obj)} - value: {order_obj}")
            description = t.description or 'Aucune description'
            reference = t.reference or 'N/A'
            heure = t.created_at.strftime('%H:%M') if t.created_at else 'N/A'
            transaction_type = t.get_transaction_type_display() or 'N/A'
            statut = t.get_status_display() or 'N/A'
            transactions_wallet.append({
                'reference': reference,
                'heure': heure,
                'type': transaction_type,
                'montant': t.amount,
                'montant_fmt': f"{t.amount:,.0f} XAF",
                'description': description,
                'statut': statut,
                'statut_badge': 'success' if t.status == 'COMPLETED' else 'secondary',
                'client': client,
                'client_obj': client_obj,
                'client_phone': phone,
                'order_number': order_number,
                'order_obj': order_obj,
                'created_at': t.created_at,
                'transaction_type': transaction_type,
                'status': t.status,
                'order_details': order_details,
            })
        # Paiements espèces
        for t in UserTransaction.objects.filter(
            wallet_content_type=wallet_ct,
            wallet_object_id=wallet.id,
            transaction_type='CASH_PAYMENT',
            status='COMPLETED',
            created_at__date=today
        ).order_by('-created_at'):
            client = 'Non renseigné'
            client_obj = None
            phone = 'Non renseigné'
            order_number = 'Aucune commande'
            order_obj = None
            order_details = None
            if hasattr(t, 'content_object') and t.content_object:
                order = t.content_object
                order_obj = order
                if hasattr(order, 'customer') and order.customer:
                    client_obj = order.customer
                    if hasattr(client_obj, 'get_full_name'):
                        client = client_obj.get_full_name() or getattr(client_obj, 'username', 'Non renseigné')
                    else:
                        client = str(client_obj)
                    phone = getattr(client_obj, 'phone_number', '') or 'Non renseigné'
                order_number = getattr(order, 'order_number', '') or 'Aucune commande'
                order_details = {
                    'order_number': getattr(order, 'order_number', ''),
                    'order_type': getattr(order, 'order_type', ''),
                    'status': getattr(order, 'status', ''),
                    'payment_status': getattr(order, 'payment_status', ''),
                    'total_amount': getattr(order, 'total_amount', ''),
                    'created_at': getattr(order, 'created_at', None),
                    'customer': client,
                    'customer_phone': phone,
                    'items': [
                        {
                            'name': getattr(item.menu_item, 'name', ''),
                            'quantity': item.quantity,
                            'unit_price': item.unit_price,
                            'total_price': item.total_price
                        } for item in (order.items.all() if hasattr(order, 'items') and hasattr(order.items, 'all') else [])
                    ]
                }
            # Log pour debug
            if client_obj is not None:
                print(f"[DEBUG] client_obj type: {type(client_obj)} - value: {client_obj}")
            if order_obj is not None:
                print(f"[DEBUG] order_obj type: {type(order_obj)} - value: {order_obj}")
            description = t.description or 'Aucune description'
            reference = t.reference or 'N/A'
            heure = t.created_at.strftime('%H:%M') if t.created_at else 'N/A'
            transaction_type = t.get_transaction_type_display() or 'N/A'
            statut = t.get_status_display() or 'N/A'
            transactions_cash.append({
                'reference': reference,
                'heure': heure,
                'type': transaction_type,
                'montant': t.amount,
                'montant_fmt': f"{t.amount:,.0f} XAF",
                'description': description,
                'statut': statut,
                'statut_badge': 'success' if t.status == 'COMPLETED' else 'secondary',
                'client': client,
                'client_obj': client_obj,
                'client_phone': phone,
                'order_number': order_number,
                'order_obj': order_obj,
                'created_at': t.created_at,
                'transaction_type': transaction_type,
                'status': t.status,
                'order_details': order_details,
            })
    context['transactions_wallet'] = transactions_wallet
    context['transactions_cash'] = transactions_cash
    
    can_create_order = (location.business.owner == request.user) or has_any_permission(request.user, location)
    context['can_create_order'] = can_create_order
    
    return render(request, template_name, context)

@login_required
def business_location_wallet_api(request, pk):
    """API JSON pour le solde et les transactions du wallet d'une business location."""
    location = get_object_or_404(BusinessLocation, pk=pk)
    wallet = getattr(location, 'wallet', None)
    business_wallet_balance = wallet.balance if wallet else 0
    
    # Transactions du jour séparées par type
    wallet_transactions = []
    cash_transactions = []
    total_wallet_today = 0
    total_cash_today = 0
    
    if wallet:
        wallet_ct = ContentType.objects.get_for_model(wallet)
        today = timezone.now().date()
        
        # Transactions PAYMENT (paiements wallet des clients)
        wallet_transactions_data = UserTransaction.objects.filter(
            wallet_content_type=wallet_ct,
            wallet_object_id=wallet.id,
            transaction_type='PAYMENT',
            status='COMPLETED',
            created_at__date=today
        ).order_by('-created_at')[:5]
        
        for t in wallet_transactions_data:
            wallet_transactions.append({
                'heure': t.created_at.strftime('%H:%M'),
                'type': 'Paiement Wallet',
                'montant': float(t.amount),
                'description': t.description,
            })
            total_wallet_today += float(t.amount)
        
        # Transactions CASH_PAYMENT (paiements espèces des clients)
        cash_transactions_data = UserTransaction.objects.filter(
            wallet_content_type=wallet_ct,
            wallet_object_id=wallet.id,
            transaction_type='CASH_PAYMENT',
            status='COMPLETED',
            created_at__date=today
        ).order_by('-created_at')[:5]
        
        for t in cash_transactions_data:
            cash_transactions.append({
                'heure': t.created_at.strftime('%H:%M'),
                'type': 'Paiement Espèces',
                'montant': float(t.amount),
                'description': t.description,
            })
            total_cash_today += float(t.amount)
    
    return JsonResponse({
        'business_wallet_balance': float(business_wallet_balance),
        'total_wallet_today': total_wallet_today,
        'total_cash_today': total_cash_today,
        'total_today': total_wallet_today + total_cash_today,
        'wallet_transactions': wallet_transactions,
        'cash_transactions': cash_transactions,
    })

@login_required
def finalize_wallet_transaction(request):
    """Finalise une transaction PENDING du wallet business location (paiement en espèces)."""
    if request.method != 'POST' or not request.is_ajax():
        return JsonResponse({'error': 'Méthode non autorisée.'}, status=405)
    transaction_id = request.POST.get('transaction_id')
    if not transaction_id:
        return JsonResponse({'error': 'ID de transaction manquant.'}, status=400)
    try:
        transaction = UserTransaction.objects.get(id=transaction_id, status='HOLD')
        # Vérifier que l'utilisateur a le droit (staff ou owner du business location)
        wallet = transaction.wallet
        location = getattr(wallet, 'business_location', None)
        if not location or (request.user != location.business.owner and not request.user.is_staff):
            return JsonResponse({'error': 'Permission refusée.'}, status=403)
        # Finaliser la transaction
        #
        transaction.status = 'COMPLETED'
        transaction.description += ' (Paiement finalisé en espèces)'
        transaction.save()
        # Mettre à jour le solde
        from apps.wallets.services.wallet_service import WalletService
        WalletService.update_wallet_balance(wallet, transaction.amount, 'add')
        # Recalculer le solde et le total du jour
        from django.contrib.contenttypes.models import ContentType
        from django.utils import timezone
        wallet_ct = ContentType.objects.get_for_model(wallet)
        today = timezone.now().date()
        solde_wallet = wallet.balance
        total_day = UserTransaction.objects.filter(
            wallet_content_type=wallet_ct,
            wallet_object_id=wallet.id,
            status='COMPLETED',
            created_at__date=today
        ).aggregate(total=Sum('amount'))['total'] or 0
        return JsonResponse({
            'success': True,
            'solde_wallet': float(solde_wallet),
            'total_day': float(total_day),
            'transaction_id': transaction.id
        })
    except UserTransaction.DoesNotExist:
        return JsonResponse({'error': 'Transaction introuvable ou déjà finalisée.'}, status=404)

@require_POST
@login_required
def create_restaurant_order_from_dashboard(request, pk):
    """
    Traite la création d'une commande depuis la modale du dashboard restaurant.
    """
    location = get_object_or_404(BusinessLocation, pk=pk)
    menu_items = MenuItem.objects.filter(business_location=location)
    menu_items_in_stock = menu_items.filter(is_available=True, stock_quantity__gt=0)

    order_form = CustomRestaurantOrderForm(request.POST, business_location=location)
    customer_form = OrderCustomerForm(request.POST)
    if order_form.is_valid() and customer_form.is_valid():
        try:
            # Recherche ou création du client
            email = customer_form.cleaned_data['email']
            phone = customer_form.cleaned_data['phone_number']
            user_qs = User.objects.filter(email=email)
            if not user_qs.exists() and phone:
                user_qs = User.objects.filter(phone_number=phone)
            if user_qs.exists():
                customer = user_qs.first()
            else:
                customer = User.objects.create(
                    first_name=customer_form.cleaned_data['first_name'],
                    last_name=customer_form.cleaned_data['last_name'],
                    email=email,
                    phone_number=phone,
                    username=email or phone or f'user_{User.objects.count()+1}'
                )
            # Créer la commande principale
            order = order_form.save(commit=False)
            order.customer = customer
            order.business_location = location
            order.status = 'READY'
            order.payment_status = 'PAID'
            order.payment_method = 'CASH'
            # Générer un numéro de commande unique
            from django.utils.crypto import get_random_string
            while True:
                order_number = f"ORD{get_random_string(8).upper()}"
                if not RestaurantOrder.objects.filter(order_number=order_number).exists():
                    break
            order.order_number = order_number
            # Calcule le sous-total avant de sauvegarder la commande
            order.subtotal = sum(
                menu_items_in_stock.get(id=item_id).price * int(request.POST.get(f'quantity_{item_id}', 1))
                for item_id in request.POST.getlist('menu_items')
            )
            # Calcule le total_amount avant de sauvegarder la commande
            try:
                order.calculate_total()
            except Exception:
                # Si la méthode n'existe pas, calcule manuellement
                order.total_amount = order.subtotal
            order.save()

            # Crée la transaction espèces automatiquement
            from apps.wallets.services.wallet_service import WalletService
            wallet, _ = WalletService.get_or_create_business_wallet(location.business)
            from django.utils.crypto import get_random_string
            reference = get_random_string(16)
            UserTransaction.objects.create(
                wallet_content_type=ContentType.objects.get_for_model(wallet),
                wallet_object_id=wallet.id,
                content_type=ContentType.objects.get_for_model(order),
                object_id=order.id,
                transaction_type='CASH_PAYMENT',
                amount=order.total_amount,
                status='COMPLETED',
                reference=reference,
                description=f'Paiement espèces pour commande {order.order_number}'
            )

            print(f"Order created with ID: {order.id}")
            # Créer les OrderItem à partir des plats sélectionnés
            menu_item_ids = request.POST.getlist('menu_items')
            for item_id in menu_item_ids:
                try:
                    menu_item = menu_items_in_stock.get(id=item_id)
                    quantity = int(request.POST.get(f'quantity_{item_id}', 1))
                    if quantity > 0 and quantity <= menu_item.stock_quantity:
                        OrderItem.objects.create(
                            restaurant_order=order,
                            menu_item=menu_item,
                            quantity=quantity,
                            unit_price=menu_item.price,
                            total_price=menu_item.price * quantity
                        )
                        menu_item.stock_quantity -= quantity
                        if menu_item.stock_quantity == 0:
                            menu_item.is_available = False
                        menu_item.save()
                except MenuItem.DoesNotExist:
                    continue
            order.calculate_total()
            order.save()
            messages.success(request, _('Order created successfully.'))
            # Redirige vers la liste filtrée des commandes de ce restaurant
            return redirect(f"{reverse('orders:order_list')}?location={location.pk}")
        except Exception as e:
            messages.error(request, str(e))
    else:
        # Si le formulaire est invalide, tu peux rediriger vers le dashboard avec les erreurs en messages
        messages.error(request, _("Erreur de validation du formulaire."))
    return redirect(reverse('business:business_location_dashboard', args=[location.pk]))

@login_required
def financial_dashboard(request):
    """
    Dashboard financier pour gérer les fonds de tous les établissements
    """
    # Récupérer tous les établissements de l'utilisateur
    owned_businesses = Business.objects.filter(owner=request.user)
    business_locations = BusinessLocation.objects.filter(
        business__in=owned_businesses
    ).prefetch_related('business', 'wallet')
    
    # Paramètres de filtrage
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')
    business_type = request.GET.get('business_type')
    
    # Convertir les dates
    if start_date:
        try:
            start_date = datetime.strptime(start_date, '%Y-%m-%d').date()
        except ValueError:
            start_date = None
    if end_date:
        try:
            end_date = datetime.strptime(end_date, '%Y-%m-%d').date()
        except ValueError:
            end_date = None
    
    # Filtrer par type d'établissement
    if business_type:
        business_locations = business_locations.filter(business_location_type=business_type)
    
    # Calculer les données financières pour chaque établissement
    locations_data = []
    total_wallet_global = 0
    total_cash_global = 0
    total_global = 0
    
    for location in business_locations:
        wallet = getattr(location, 'wallet', None)
        wallet_balance = wallet.balance if wallet else 0
        
        # Calculer les montants par type de transaction
        wallet_amount = 0
        cash_amount = 0
        
        if wallet:
            wallet_ct = ContentType.objects.get_for_model(wallet)
            
            # Filtres de date pour les transactions
            wallet_transactions = UserTransaction.objects.filter(
                wallet_content_type=wallet_ct,
                wallet_object_id=wallet.id,
                transaction_type='PAYMENT',
                status='COMPLETED'
            )
            cash_transactions = UserTransaction.objects.filter(
                wallet_content_type=wallet_ct,
                wallet_object_id=wallet.id,
                transaction_type='CASH_PAYMENT',
                status='COMPLETED'
            )
            
            if start_date:
                wallet_transactions = wallet_transactions.filter(created_at__date__gte=start_date)
                cash_transactions = cash_transactions.filter(created_at__date__gte=start_date)
            if end_date:
                wallet_transactions = wallet_transactions.filter(created_at__date__lte=end_date)
                cash_transactions = cash_transactions.filter(created_at__date__lte=end_date)
            
            wallet_amount = wallet_transactions.aggregate(total=Sum('amount'))['total'] or 0
            cash_amount = cash_transactions.aggregate(total=Sum('amount'))['total'] or 0
        
        total_amount = wallet_amount + cash_amount
        
        # Ajouter aux totaux globaux
        total_wallet_global += wallet_amount
        total_cash_global += cash_amount
        total_global += total_amount
        
        locations_data.append({
            'location': location,
            'wallet_balance': wallet_balance,
            'wallet_amount': wallet_amount,
            'cash_amount': cash_amount,
            'total_amount': total_amount,
            'has_high_balance': wallet_balance > 100000,  # Alerte si > 100k XAF
        })
    
    # Données pour le graphe des tendances (12 derniers mois)
    # 1. Graphe cumulatif (solde qui s'accumule mois après mois)
    chart_data_cumulative = []
    cumulative_total = 0
    today = timezone.now().date().replace(day=1)
    
    for i in range(12):
        month_start = today - relativedelta(months=11 - i)
        next_month = (month_start + relativedelta(months=1))
        month_total = 0
        
        for location in business_locations:
            wallet = getattr(location, 'wallet', None)
            if wallet:
                wallet_ct = ContentType.objects.get_for_model(wallet)
                month_transactions = UserTransaction.objects.filter(
                    wallet_content_type=wallet_ct,
                    wallet_object_id=wallet.id,
                    transaction_type__in=['PAYMENT', 'CASH_PAYMENT'],
                    status='COMPLETED',
                    created_at__date__gte=month_start,
                    created_at__date__lt=next_month
                )
                month_total += month_transactions.aggregate(total=Sum('amount'))['total'] or 0
        
        cumulative_total += month_total
        chart_data_cumulative.append({
            'month': month_start.strftime('%B %Y'),
            'total': float(cumulative_total)
        })
    
    chart_data_cumulative.reverse()  # Du plus ancien au plus récent
    
    # 2. Graphe par type de transaction (wallet vs espèces)
    chart_data_by_type = []
    today = timezone.now().date().replace(day=1)
    
    for i in range(12):
        month_start = today - relativedelta(months=11 - i)
        next_month = (month_start + relativedelta(months=1))
        month_wallet_total = 0
        month_cash_total = 0
        
        for location in business_locations:
            wallet = getattr(location, 'wallet', None)
            if wallet:
                wallet_ct = ContentType.objects.get_for_model(wallet)
                
                # Transactions wallet
                wallet_transactions = UserTransaction.objects.filter(
                    wallet_content_type=wallet_ct,
                    wallet_object_id=wallet.id,
                    transaction_type='PAYMENT',
                    status='COMPLETED',
                    created_at__date__gte=month_start,
                    created_at__date__lt=next_month
                )
                month_wallet_total += wallet_transactions.aggregate(total=Sum('amount'))['total'] or 0
                
                # Transactions espèces
                cash_transactions = UserTransaction.objects.filter(
                    wallet_content_type=wallet_ct,
                    wallet_object_id=wallet.id,
                    transaction_type='CASH_PAYMENT',
                    status='COMPLETED',
                    created_at__date__gte=month_start,
                    created_at__date__lt=next_month
                )
                month_cash_total += cash_transactions.aggregate(total=Sum('amount'))['total'] or 0
        
        chart_data_by_type.append({
            'month': month_start.strftime('%B %Y'),
            'wallet': float(month_wallet_total),
            'cash': float(month_cash_total)
        })
    
    chart_data_by_type.reverse()  # Du plus ancien au plus récent
    
    # Traitement du retrait de fonds
    if request.method == 'POST' and 'withdraw' in request.POST:
        location_id = request.POST.get('location_id')
        amount = request.POST.get('amount')
        password = request.POST.get('password')
        
        try:
            location = BusinessLocation.objects.get(
                id=location_id,
                business__owner=request.user
            )
            amount = Decimal(amount)
            
            # Validation du montant
            if amount <= 0:
                messages.error(request, _("Le montant doit être positif."))
            elif amount > location.wallet.balance:
                messages.error(request, _("Le montant dépasse le solde disponible."))
            elif not request.user.check_password(password):
                messages.error(request, _("Mot de passe incorrect."))
            else:
                # Effectuer le retrait
                from apps.wallets.services.wallet_service import WalletService
                if WalletService.update_wallet_balance(location.wallet, amount, 'subtract'):
                    # Créer la transaction de retrait
                    UserTransaction.objects.create(
                        wallet_content_type=ContentType.objects.get_for_model(location.wallet),
                        wallet_object_id=location.wallet.id,
                        transaction_type='WITHDRAWAL',
                        amount=amount,
                        status='COMPLETED',
                        reference=f"WIT-{location.id}-{uuid.uuid4().hex[:8]}",
                        description=f"Retrait de fonds - {location.name}",
                        created_at=timezone.now()
                    )
                    messages.success(request, f"Retrait de {amount:,.0f} XAF effectué avec succès.")
                else:
                    messages.error(request, _("Erreur lors du retrait."))
                    
        except (BusinessLocation.DoesNotExist, ValueError, TypeError):
            messages.error(request, _("Données invalides."))
        
        return redirect('business:financial_dashboard')
    
    # Historique des retraits
    withdrawal_history = []
    for location in business_locations:
        wallet = getattr(location, 'wallet', None)
        if wallet:
            wallet_ct = ContentType.objects.get_for_model(wallet)
            withdrawals = UserTransaction.objects.filter(
                wallet_content_type=wallet_ct,
                wallet_object_id=wallet.id,
                transaction_type='WITHDRAWAL',
                status='COMPLETED'
            ).order_by('-created_at')[:5]
            
            for withdrawal in withdrawals:
                withdrawal_history.append({
                    'location': location,
                    'amount': withdrawal.amount,
                    'date': withdrawal.created_at,
                    'reference': withdrawal.reference
                })
    
    withdrawal_history.sort(key=lambda x: x['date'], reverse=True)
    
    context = {
        'locations_data': locations_data,
        'total_wallet_global': total_wallet_global,
        'total_cash_global': total_cash_global,
        'total_global': total_global,
        'chart_data_cumulative': json.dumps(chart_data_cumulative),  # Correction ici
        'chart_data_by_type': json.dumps(chart_data_by_type),  # Correction ici
        'withdrawal_history': withdrawal_history[:10],  # 10 derniers retraits
        'start_date': start_date,
        'end_date': end_date,
        'business_type': business_type,
        'business_types': BusinessLocation.BUSINESS_TYPES,
        'has_high_balances': any(loc['has_high_balance'] for loc in locations_data),
    }
    
    return render(request, 'business/financial_dashboard.html', context)
