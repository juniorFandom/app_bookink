from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator
from django.db.models import Count, Q, Avg
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.db import transaction
from django.utils import timezone

from ...models import BusinessLocation, BusinessLocationImage
from ...forms import BusinessLocationForm
from ...services.services import BusinessLocationService


def is_staff_user(user):
    """Check if user is staff member"""
    return user.is_authenticated and user.is_staff


@login_required
@user_passes_test(is_staff_user)
def location_dashboard(request):
    """Admin dashboard for business location management"""
    # Statistics
    total_locations = BusinessLocation.objects.count()
    active_locations = BusinessLocation.objects.filter(is_active=True).count()
    verified_locations = BusinessLocation.objects.filter(is_verified=True).count()
    featured_locations = BusinessLocation.objects.filter(featured=True).count()
    
    # Locations by type
    type_stats = BusinessLocation.objects.values('business_location_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Recent locations
    recent_locations = BusinessLocation.objects.select_related('business').order_by('-created_at')[:5]
    
    # Average ratings
    avg_rating = BusinessLocation.objects.aggregate(
        avg_rating=Avg('reviews__rating')
    )['avg_rating'] or 0
    
    context = {
        'total_locations': total_locations,
        'active_locations': active_locations,
        'verified_locations': verified_locations,
        'featured_locations': featured_locations,
        'type_stats': type_stats,
        'recent_locations': recent_locations,
        'avg_rating': round(avg_rating, 1),
    }
    return render(request, 'business/admin/location_dashboard.html', context)


@login_required
@user_passes_test(is_staff_user)
def location_list(request):
    """List all business locations with filters and search"""
    # Get filter parameters
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    verified = request.GET.get('verified', '')
    business_type = request.GET.get('business_type', '')
    featured = request.GET.get('featured', '')
    
    # Base queryset
    locations = BusinessLocation.objects.select_related('business', 'owner').order_by('-created_at')
    
    # Apply filters
    if search:
        locations = locations.filter(
            Q(name__icontains=search) |
            Q(business__name__icontains=search) |
            Q(phone__icontains=search) |
            Q(email__icontains=search) |
            Q(registration_number__icontains=search)
        )
    
    if status:
        if status == 'active':
            locations = locations.filter(is_active=True)
        elif status == 'inactive':
            locations = locations.filter(is_active=False)
    
    if verified:
        if verified == 'verified':
            locations = locations.filter(is_verified=True)
        elif verified == 'unverified':
            locations = locations.filter(is_verified=False)
    
    if business_type:
        locations = locations.filter(business_location_type=business_type)
    
    if featured:
        if featured == 'featured':
            locations = locations.filter(featured=True)
        elif featured == 'not_featured':
            locations = locations.filter(featured=False)
    
    # Pagination
    paginator = Paginator(locations, 20)
    page = request.GET.get('page')
    locations = paginator.get_page(page)
    
    context = {
        'locations': locations,
        'search': search,
        'status': status,
        'verified': verified,
        'business_type': business_type,
        'featured': featured,
        'business_types': BusinessLocation.BUSINESS_TYPES,
    }
    return render(request, 'business/admin/location_list.html', context)


@login_required
@user_passes_test(is_staff_user)
def location_create(request):
    """Create a new business location"""
    if request.method == 'POST':
        form = BusinessLocationForm(request.POST, request.FILES)
        if form.is_valid():
            location = form.save()
            messages.success(request, _('Business location created successfully!'))
            return redirect('business:admin_location_detail', pk=location.pk)
    else:
        form = BusinessLocationForm()
    
    context = {
        'form': form,
        'title': _('Create New Business Location'),
        'is_create': True,
    }
    return render(request, 'business/admin/location_form.html', context)


@login_required
@user_passes_test(is_staff_user)
def location_detail(request, pk):
    """View business location details"""
    location = get_object_or_404(BusinessLocation, pk=pk)
    
    # Get related data
    images = location.images.all()
    reviews = location.reviews.all().order_by('-created_at')[:10]
    total_reviews = location.reviews.count()
    avg_rating = location.reviews.aggregate(avg=Avg('rating'))['avg'] or 0
    
    # Rating distribution
    rating_distribution = location.reviews.values('rating').annotate(
        count=Count('id')
    ).order_by('rating')
    
    context = {
        'location': location,
        'images': images,
        'reviews': reviews,
        'total_reviews': total_reviews,
        'avg_rating': round(avg_rating, 1),
        'rating_distribution': rating_distribution,
    }
    return render(request, 'business/admin/location_detail.html', context)


@login_required
@user_passes_test(is_staff_user)
def location_edit(request, pk):
    """Edit an existing business location"""
    location = get_object_or_404(BusinessLocation, pk=pk)
    
    if request.method == 'POST':
        form = BusinessLocationForm(request.POST, request.FILES, instance=location)
        if form.is_valid():
            form.save()
            messages.success(request, _('Business location updated successfully!'))
            return redirect('business:admin_location_detail', pk=location.pk)
    else:
        form = BusinessLocationForm(instance=location)
    
    context = {
        'form': form,
        'location': location,
        'title': _('Edit Business Location'),
        'is_create': False,
    }
    return render(request, 'business/admin/location_form.html', context)


@login_required
@user_passes_test(is_staff_user)
@require_POST
def location_delete(request, pk):
    """Delete a business location"""
    location = get_object_or_404(BusinessLocation, pk=pk)
    
    try:
        with transaction.atomic():
            # Check if location has active bookings or reviews
            if location.reviews.exists():
                messages.error(request, _('Cannot delete location with reviews.'))
                return redirect('business:admin_location_detail', pk=location.pk)
            
            location.delete()
            messages.success(request, _('Business location deleted successfully!'))
            return redirect('business:admin_location_list')
    except Exception as e:
        messages.error(request, _('Error deleting business location: ') + str(e))
        return redirect('business:admin_location_detail', pk=location.pk)


@login_required
@user_passes_test(is_staff_user)
@require_POST
def location_toggle_status(request, pk):
    """Toggle business location active status"""
    location = get_object_or_404(BusinessLocation, pk=pk)
    
    try:
        location.is_active = not location.is_active
        location.save()
        
        status = _('activated') if location.is_active else _('deactivated')
        messages.success(request, _(f'Business location {status} successfully!'))
        
        return JsonResponse({
            'success': True,
            'is_active': location.is_active,
            'message': f'Business location {status} successfully!'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@user_passes_test(is_staff_user)
@require_POST
def location_toggle_verification(request, pk):
    """Toggle business location verification status"""
    location = get_object_or_404(BusinessLocation, pk=pk)
    
    try:
        location.is_verified = not location.is_verified
        location.save()
        
        status = _('verified') if location.is_verified else _('unverified')
        messages.success(request, _(f'Business location {status} successfully!'))
        
        return JsonResponse({
            'success': True,
            'is_verified': location.is_verified,
            'message': f'Business location {status} successfully!'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@user_passes_test(is_staff_user)
@require_POST
def location_toggle_featured(request, pk):
    """Toggle business location featured status"""
    location = get_object_or_404(BusinessLocation, pk=pk)
    
    try:
        location.featured = not location.featured
        location.save()
        
        status = _('featured') if location.featured else _('unfeatured')
        messages.success(request, _(f'Business location {status} successfully!'))
        
        return JsonResponse({
            'success': True,
            'featured': location.featured,
            'message': f'Business location {status} successfully!'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@user_passes_test(is_staff_user)
@require_POST
def location_image_delete(request, pk, image_id):
    """Delete a business location image"""
    location = get_object_or_404(BusinessLocation, pk=pk)
    image = get_object_or_404(BusinessLocationImage, pk=image_id, business_location=location)
    
    try:
        image.delete()
        messages.success(request, _('Image deleted successfully!'))
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@user_passes_test(is_staff_user)
@require_POST
def location_image_primary(request, pk, image_id):
    """Set image as primary"""
    location = get_object_or_404(BusinessLocation, pk=pk)
    image = get_object_or_404(BusinessLocationImage, pk=image_id, business_location=location)
    
    try:
        # Set all images as non-primary first
        location.images.update(is_primary=False)
        # Set this image as primary
        image.is_primary = True
        image.save()
        
        messages.success(request, _('Primary image updated successfully!'))
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500) 