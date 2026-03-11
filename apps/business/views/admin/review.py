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

from ...models import BusinessReview, BusinessLocation
from ...forms import BusinessReviewForm


def is_staff_user(user):
    """Check if user is staff member"""
    return user.is_authenticated and user.is_staff


@login_required
@user_passes_test(is_staff_user)
def review_dashboard(request):
    """Admin dashboard for business review management"""
    # Statistics
    total_reviews = BusinessReview.objects.count()
    recent_reviews = BusinessReview.objects.filter(
        created_at__gte=timezone.now() - timezone.timedelta(days=30)
    ).count()
    
    # Average ratings
    avg_overall = BusinessReview.objects.aggregate(avg=Avg('rating'))['avg'] or 0
    avg_service = BusinessReview.objects.aggregate(avg=Avg('service_rating'))['avg'] or 0
    avg_value = BusinessReview.objects.aggregate(avg=Avg('value_rating'))['avg'] or 0
    
    # Reviews by rating
    rating_distribution = BusinessReview.objects.values('rating').annotate(
        count=Count('id')
    ).order_by('rating')
    
    # Recent reviews
    recent_review_list = BusinessReview.objects.select_related(
        'business_location', 'reviewer'
    ).order_by('-created_at')[:10]
    
    context = {
        'total_reviews': total_reviews,
        'recent_reviews': recent_reviews,
        'avg_overall': round(avg_overall, 1),
        'avg_service': round(avg_service, 1),
        'avg_value': round(avg_value, 1),
        'rating_distribution': rating_distribution,
        'recent_review_list': recent_review_list,
    }
    return render(request, 'business/admin/review_dashboard.html', context)


@login_required
@user_passes_test(is_staff_user)
def review_list(request):
    """List all business reviews with filters and search"""
    # Get filter parameters
    search = request.GET.get('search', '')
    rating = request.GET.get('rating', '')
    location = request.GET.get('location', '')
    visit_type = request.GET.get('visit_type', '')
    
    # Base queryset
    reviews = BusinessReview.objects.select_related(
        'business_location', 'business_location__business', 'reviewer'
    ).order_by('-created_at')
    
    # Apply filters
    if search:
        reviews = reviews.filter(
            Q(title__icontains=search) |
            Q(content__icontains=search) |
            Q(business_location__name__icontains=search) |
            Q(business_location__business__name__icontains=search) |
            Q(reviewer__username__icontains=search) |
            Q(reviewer__first_name__icontains=search) |
            Q(reviewer__last_name__icontains=search)
        )
    
    if rating:
        reviews = reviews.filter(rating=rating)
    
    if location:
        reviews = reviews.filter(business_location_id=location)
    
    if visit_type:
        reviews = reviews.filter(visit_type=visit_type)
    
    # Pagination
    paginator = Paginator(reviews, 20)
    page = request.GET.get('page')
    reviews = paginator.get_page(page)
    
    # Get locations for filter dropdown
    locations = BusinessLocation.objects.filter(is_active=True).order_by('name')
    
    context = {
        'reviews': reviews,
        'search': search,
        'rating': rating,
        'location': location,
        'visit_type': visit_type,
        'locations': locations,
        'visit_types': BusinessReview._meta.get_field('visit_type').choices,
    }
    return render(request, 'business/admin/review_list.html', context)


@login_required
@user_passes_test(is_staff_user)
def review_detail(request, pk):
    """View business review details"""
    review = get_object_or_404(BusinessReview, pk=pk)
    
    context = {
        'review': review,
    }
    return render(request, 'business/admin/review_detail.html', context)


@login_required
@user_passes_test(is_staff_user)
def review_edit(request, pk):
    """Edit an existing business review"""
    review = get_object_or_404(BusinessReview, pk=pk)
    
    if request.method == 'POST':
        form = BusinessReviewForm(request.POST, instance=review)
        if form.is_valid():
            form.save()
            messages.success(request, _('Review updated successfully!'))
            return redirect('business:admin_review_detail', pk=review.pk)
    else:
        form = BusinessReviewForm(instance=review)
    
    context = {
        'form': form,
        'review': review,
        'title': _('Edit Review'),
    }
    return render(request, 'business/admin/review_form.html', context)


@login_required
@user_passes_test(is_staff_user)
@require_POST
def review_delete(request, pk):
    """Delete a business review"""
    review = get_object_or_404(BusinessReview, pk=pk)
    
    try:
        review.delete()
        messages.success(request, _('Review deleted successfully!'))
        return redirect('business:admin_review_list')
    except Exception as e:
        messages.error(request, _('Error deleting review: ') + str(e))
        return redirect('business:admin_review_detail', pk=review.pk)


@login_required
@user_passes_test(is_staff_user)
@require_POST
def review_approve(request, pk):
    """Approve a business review"""
    review = get_object_or_404(BusinessReview, pk=pk)
    
    try:
        review.is_approved = True
        review.save()
        messages.success(request, _('Review approved successfully!'))
        
        return JsonResponse({
            'success': True,
            'is_approved': review.is_approved,
            'message': 'Review approved successfully!'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@user_passes_test(is_staff_user)
@require_POST
def review_reject(request, pk):
    """Reject a business review"""
    review = get_object_or_404(BusinessReview, pk=pk)
    
    try:
        review.is_approved = False
        review.save()
        messages.success(request, _('Review rejected successfully!'))
        
        return JsonResponse({
            'success': True,
            'is_approved': review.is_approved,
            'message': 'Review rejected successfully!'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)


@login_required
@user_passes_test(is_staff_user)
def review_analytics(request):
    """Review analytics and statistics"""
    # Overall statistics
    total_reviews = BusinessReview.objects.count()
    approved_reviews = BusinessReview.objects.filter(is_approved=True).count()
    pending_reviews = BusinessReview.objects.filter(is_approved__isnull=True).count()
    rejected_reviews = BusinessReview.objects.filter(is_approved=False).count()
    
    # Rating statistics
    rating_stats = BusinessReview.objects.values('rating').annotate(
        count=Count('id')
    ).order_by('rating')
    
    # Service rating statistics
    service_rating_stats = BusinessReview.objects.values('service_rating').annotate(
        count=Count('id')
    ).order_by('service_rating')
    
    # Value rating statistics
    value_rating_stats = BusinessReview.objects.values('value_rating').annotate(
        count=Count('id')
    ).order_by('value_rating')
    
    # Visit type statistics
    visit_type_stats = BusinessReview.objects.values('visit_type').annotate(
        count=Count('id')
    ).order_by('visit_type')
    
    # Monthly review trends
    monthly_trends = BusinessReview.objects.extra(
        select={'month': "EXTRACT(month FROM created_at)"}
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    context = {
        'total_reviews': total_reviews,
        'approved_reviews': approved_reviews,
        'pending_reviews': pending_reviews,
        'rejected_reviews': rejected_reviews,
        'rating_stats': rating_stats,
        'service_rating_stats': service_rating_stats,
        'value_rating_stats': value_rating_stats,
        'visit_type_stats': visit_type_stats,
        'monthly_trends': monthly_trends,
    }
    return render(request, 'business/admin/review_analytics.html', context) 