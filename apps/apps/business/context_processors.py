from datetime import datetime
from .models import Business, BusinessType
from .forms import BusinessSearchForm

def business_context(request):
    """Add business-related context to all templates."""
    context = {
        'business_types': BusinessType.choices,
        'business_search_form': BusinessSearchForm(
            initial={
                'query': request.GET.get('query', ''),
                'business_type': request.GET.get('business_type', ''),
                'city': request.GET.get('city', ''),
                'rating': request.GET.get('rating', ''),
                'sort_by': request.GET.get('sort_by', ''),
                'verified_only': request.GET.get('verified_only', False),
            }
        ),
        'current_time': datetime.now().time(),
        'current_day': datetime.now().strftime('%A').lower(),
    }

    # Add popular cities if we have businesses
    if Business.objects.exists():
        context['popular_cities'] = (
            Business.objects
            .exclude(city='')
            .values_list('city', flat=True)
            .distinct()
            .order_by('city')[:10]
        )

    return context 