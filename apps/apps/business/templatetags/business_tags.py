from django import template
from django.utils.safestring import mark_safe
from django.contrib.auth import get_user_model
from ..models import BusinessLocation, BusinessPermission
from ..views.permissions import check_permission, has_any_permission, get_accessible_locations

register = template.Library()

User = get_user_model()

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary using bracket notation."""
    return dictionary.get(key)

@register.filter
def get_form_for_amenity(formset, amenity):
    """Get the form from a formset that corresponds to a specific amenity."""
    for form in formset:
        if form.instance and form.instance.amenity == amenity:
            return form
        if not form.instance and form.initial and form.initial.get('amenity') == amenity.id:
            return form
    return None

@register.filter
def multiply(value, arg):
    """Multiply the value by the argument."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ''

@register.simple_tag
def rating_stars(rating, max_rating=5):
    """Generate HTML for displaying rating stars."""
    if not rating:
        return mark_safe('<span class="text-muted">No rating</span>')

    full_stars = int(rating)
    half_star = rating % 1 >= 0.5
    empty_stars = max_rating - full_stars - (1 if half_star else 0)

    stars_html = []
    
    # Add full stars
    for _ in range(full_stars):
        stars_html.append('<i class="fas fa-star text-warning"></i>')
    
    # Add half star if needed
    if half_star:
        stars_html.append('<i class="fas fa-star-half-alt text-warning"></i>')
    
    # Add empty stars
    for _ in range(empty_stars):
        stars_html.append('<i class="far fa-star text-warning"></i>')

    return mark_safe(''.join(stars_html))

@register.simple_tag
def business_hours_status(business, current_time=None):
    """Return the current open/closed status of a business."""
    is_open = business.is_open(current_time)
    next_status = business.get_next_status_change(current_time)

    if is_open:
        status_html = '<span class="badge bg-success">Open</span>'
        if next_status:
            status_html += f' <small class="text-muted">(Closes at {next_status.strftime("%I:%M %p")})</small>'
    else:
        status_html = '<span class="badge bg-danger">Closed</span>'
        if next_status:
            status_html += f' <small class="text-muted">(Opens at {next_status.strftime("%I:%M %p")})</small>'

    return mark_safe(status_html)

@register.filter
def format_phone(phone_number):
    """Format a phone number for display."""
    if not phone_number:
        return ''
    
    # Remove any non-digit characters
    digits = ''.join(filter(str.isdigit, str(phone_number)))
    
    if len(digits) == 10:  # Standard phone number
        return f"({digits[:3]}) {digits[3:6]}-{digits[6:]}"
    elif len(digits) == 11 and digits[0] == '1':  # Number with country code
        return f"+1 ({digits[1:4]}) {digits[4:7]}-{digits[7:]}"
    else:
        return phone_number  # Return original if format is unknown

@register.filter
def amenity_icon(amenity):
    """Return the Font Awesome icon class for an amenity."""
    if not amenity.icon:
        return 'fas fa-check'
    return amenity.icon

@register.simple_tag
def business_type_icon(business_type):
    """Return the Font Awesome icon class for a business type."""
    icons = {
        'hotel': 'fas fa-hotel',
        'restaurant': 'fas fa-utensils',
        'attraction': 'fas fa-monument',
        'tour_operator': 'fas fa-map-marked-alt',
        'transport': 'fas fa-bus',
        'shop': 'fas fa-shopping-bag',
        'service': 'fas fa-concierge-bell',
        'other': 'fas fa-store'
    }
    return icons.get(business_type, 'fas fa-store')

@register.filter
def review_summary(reviews):
    """Generate a summary of review ratings."""
    if not reviews:
        return None
    
    total = len(reviews)
    rating_counts = {i: 0 for i in range(1, 6)}
    
    for review in reviews:
        rating = int(round(review.overall_rating))
        rating_counts[rating] = rating_counts.get(rating, 0) + 1
    
    summary = {
        'total': total,
        'average': sum(r.overall_rating for r in reviews) / total,
        'distribution': {
            rating: {
                'count': count,
                'percentage': (count / total) * 100
            }
            for rating, count in rating_counts.items()
        }
    }
    
    return summary

@register.filter
def get_business_schedule(business, day_name):
    """Get the formatted schedule for a specific day."""
    try:
        schedule = business.hours.get(day_name=day_name)
        if schedule.is_closed:
            return 'Closed'
        
        hours = f"{schedule.opening_time.strftime('%I:%M %p')} - {schedule.closing_time.strftime('%I:%M %p')}"
        
        if schedule.break_start and schedule.break_end:
            hours += f"\nBreak: {schedule.break_start.strftime('%I:%M %p')} - {schedule.break_end.strftime('%I:%M %p')}"
        
        return hours
    except:
        return 'Not specified' 

@register.filter
def get_amenity_checked(assignments, amenity_id):
    """Retourne True si l'amenity est assignée à la location."""
    if not assignments:
        return False
    for a in assignments.all() if hasattr(assignments, 'all') else assignments:
        if str(a.amenity.id) == str(amenity_id):
            return True
    return False

@register.filter
def get_amenity_details(assignments, amenity_id):
    """Retourne le détail de l'amenity assignée à la location."""
    if not assignments:
        return ''
    for a in assignments.all() if hasattr(assignments, 'all') else assignments:
        if str(a.amenity.id) == str(amenity_id):
            return a.details or ''
    return ''

@register.filter
def has_permission(user, location_and_permission):
    """
    Vérifie si un utilisateur a une permission spécifique
    Usage: {% if user|has_permission:location_and_permission %}
    """
    if not user.is_authenticated:
        return False
    
    try:
        location_pk, permission_type = location_and_permission.split(':')
        location = BusinessLocation.objects.get(pk=location_pk)
        return check_permission(user, location, permission_type)
    except (ValueError, BusinessLocation.DoesNotExist):
        return False

@register.filter
def has_any_permission_for(user, location):
    """
    Vérifie si un utilisateur a au moins une permission pour un établissement
    Usage: {% if user|has_any_permission_for:location %}
    """
    if not user.is_authenticated:
        return False
    
    return has_any_permission(user, location)

@register.simple_tag
def get_user_accessible_locations(user):
    """
    Récupère tous les établissements auxquels un utilisateur a accès
    Usage: {% get_user_accessible_locations user as accessible_locations %}
    """
    return get_accessible_locations(user)

@register.simple_tag
def get_user_permissions(user):
    """
    Récupère toutes les permissions actives d'un utilisateur
    Usage: {% get_user_permissions user as user_permissions %}
    """
    if not user.is_authenticated:
        return BusinessPermission.objects.none()
    
    return BusinessPermission.objects.filter(
        user=user,
        is_active=True
    ).select_related('business_location', 'business_location__business')

@register.filter
def is_owner(user, location):
    """
    Vérifie si un utilisateur est le propriétaire d'un établissement
    Usage: {% if user|is_owner:location %}
    """
    if not user.is_authenticated:
        return False
    
    return location.business.owner == user 