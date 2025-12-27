from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils.translation import gettext_lazy as _
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.urls import reverse
from django.db import transaction
from django.utils import timezone

from ...models import Business
from ...forms import BusinessForm


def is_staff_user(user):
    """Check if user is staff member"""
    return user.is_authenticated and user.is_staff


@login_required
@user_passes_test(is_staff_user)
def business_dashboard(request):
    """Admin dashboard for business management"""
    # Statistics
    total_businesses = Business.objects.count()
    active_businesses = Business.objects.filter(is_active=True).count()
    verified_businesses = Business.objects.filter(is_verified=True).count()
    recent_businesses = Business.objects.filter(
        created_at__gte=timezone.now() - timezone.timedelta(days=30)
    ).count()
    
    # Recent businesses
    recent_business_list = Business.objects.order_by('-created_at')[:5]
    
    # Businesses by status
    status_stats = Business.objects.aggregate(
        active=Count('id', filter=Q(is_active=True)),
        inactive=Count('id', filter=Q(is_active=False)),
        verified=Count('id', filter=Q(is_verified=True)),
        unverified=Count('id', filter=Q(is_verified=False))
    )
    
    context = {
        'total_businesses': total_businesses,
        'active_businesses': active_businesses,
        'verified_businesses': verified_businesses,
        'recent_businesses': recent_businesses,
        'recent_business_list': recent_business_list,
        'status_stats': status_stats,
    }
    return render(request, 'business/admin/dashboard.html', context)


@login_required
@user_passes_test(is_staff_user)
def business_list(request):
    """List all businesses with filters and search"""
    # Get filter parameters
    search = request.GET.get('search', '')
    status = request.GET.get('status', '')
    verified = request.GET.get('verified', '')
    
    # Base queryset
    businesses = Business.objects.select_related('owner').order_by('-created_at')
    
    # Apply filters
    if search:
        businesses = businesses.filter(
            Q(name__icontains=search) |
            Q(email__icontains=search) |
            Q(phone__icontains=search) |
            Q(owner__username__icontains=search) |
            Q(owner__first_name__icontains=search) |
            Q(owner__last_name__icontains=search)
        )
    
    if status:
        if status == 'active':
            businesses = businesses.filter(is_active=True)
        elif status == 'inactive':
            businesses = businesses.filter(is_active=False)
    
    if verified:
        if verified == 'verified':
            businesses = businesses.filter(is_verified=True)
        elif verified == 'unverified':
            businesses = businesses.filter(is_verified=False)
    
    # Pagination
    paginator = Paginator(businesses, 20)
    page = request.GET.get('page')
    businesses = paginator.get_page(page)
    
    context = {
        'businesses': businesses,
        'search': search,
        'status': status,
        'verified': verified,
    }
    return render(request, 'business/admin/business_list.html', context)


@login_required
@user_passes_test(is_staff_user)
def business_create(request):
    """Create a new business"""
    if request.method == 'POST':
        form = BusinessForm(request.POST)
        if form.is_valid():
            business = form.save()
            messages.success(request, _('Business created successfully!'))
            return redirect('business:admin_business_detail', pk=business.pk)
    else:
        form = BusinessForm()
    
    context = {
        'form': form,
        'title': _('Create New Business'),
        'is_create': True,
    }
    return render(request, 'business/admin/business_form.html', context)


@login_required
@user_passes_test(is_staff_user)
def business_detail(request, pk):
    """View business details"""
    business = get_object_or_404(Business, pk=pk)
    
    # Get related data
    locations = business.locations.all()
    total_locations = locations.count()
    active_locations = locations.filter(is_active=True).count()
    
    context = {
        'business': business,
        'locations': locations,
        'total_locations': total_locations,
        'active_locations': active_locations,
    }
    return render(request, 'business/admin/business_detail.html', context)


@login_required
@user_passes_test(is_staff_user)
def business_edit(request, pk):
    """Edit an existing business"""
    business = get_object_or_404(Business, pk=pk)
    
    if request.method == 'POST':
        form = BusinessForm(request.POST, instance=business)
        if form.is_valid():
            form.save()
            messages.success(request, _('Business updated successfully!'))
            return redirect('business:admin_business_detail', pk=business.pk)
    else:
        form = BusinessForm(instance=business)
    
    context = {
        'form': form,
        'business': business,
        'title': _('Edit Business'),
        'is_create': False,
    }
    return render(request, 'business/admin/business_form.html', context)


@login_required
@user_passes_test(is_staff_user)
@require_POST
def business_delete(request, pk):
    """Delete a business"""
    business = get_object_or_404(Business, pk=pk)
    
    try:
        with transaction.atomic():
            # Check if business has active locations
            if business.locations.filter(is_active=True).exists():
                messages.error(request, _('Cannot delete business with active locations.'))
                return redirect('business:admin_business_detail', pk=business.pk)
            
            business.delete()
            messages.success(request, _('Business deleted successfully!'))
            return redirect('business:admin_business_list')
    except Exception as e:
        messages.error(request, _('Error deleting business: ') + str(e))
        return redirect('business:admin_business_detail', pk=business.pk)


@login_required
@user_passes_test(is_staff_user)
@require_POST
def business_toggle_status(request, pk):
    """Toggle business active status"""
    business = get_object_or_404(Business, pk=pk)
    
    try:
        business.is_active = not business.is_active
        business.save()
        
        status = _('activated') if business.is_active else _('deactivated')
        messages.success(request, _(f'Business {status} successfully!'))
        
        return JsonResponse({
            'success': True,
            'is_active': business.is_active,
            'message': f'Business {status} successfully!'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@user_passes_test(is_staff_user)
@require_POST
def business_toggle_verification(request, pk):
    """Toggle business verification status"""
    business = get_object_or_404(Business, pk=pk)
    
    try:
        business.is_verified = not business.is_verified
        business.save()
        
        status = _('verified') if business.is_verified else _('unverified')
        messages.success(request, _(f'Business {status} successfully!'))
        
        return JsonResponse({
            'success': True,
            'is_verified': business.is_verified,
            'message': f'Business {status} successfully!'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500) 