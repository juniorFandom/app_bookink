from django import template
from django.utils.safestring import mark_safe
from django.utils.html import escape
from django.utils.timezone import now
from datetime import datetime, timedelta

register = template.Library()

@register.filter
def currency(value):
    """Format a number as currency."""
    try:
        return f"${value:,.2f}"
    except (ValueError, TypeError):
        return ''

@register.filter
def time_since(value):
    """Return a string representing time since the given datetime."""
    if not value:
        return ''

    now_time = now()
    diff = now_time - value

    if diff.days > 365:
        years = diff.days // 365
        return f"{years} year{'s' if years != 1 else ''} ago"
    elif diff.days > 30:
        months = diff.days // 30
        return f"{months} month{'s' if months != 1 else ''} ago"
    elif diff.days > 0:
        return f"{diff.days} day{'s' if diff.days != 1 else ''} ago"
    elif diff.seconds > 3600:
        hours = diff.seconds // 3600
        return f"{hours} hour{'s' if hours != 1 else ''} ago"
    elif diff.seconds > 60:
        minutes = diff.seconds // 60
        return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
    else:
        return "just now"

@register.filter
def business_hours_today(business):
    """Return formatted business hours for today."""
    today = now().strftime('%A').lower()
    try:
        hours = business.hours.get(day_name=today)
        if hours.is_closed:
            return mark_safe('<span class="text-danger">Closed today</span>')
        
        schedule = f"{hours.opening_time.strftime('%I:%M %p')} - {hours.closing_time.strftime('%I:%M %p')}"
        if hours.break_start and hours.break_end:
            schedule += f"<br><small class='text-muted'>Break: {hours.break_start.strftime('%I:%M %p')} - {hours.break_end.strftime('%I:%M %p')}</small>"
        
        return mark_safe(schedule)
    except:
        return mark_safe('<span class="text-muted">Hours not specified</span>')

@register.filter
def highlight_search(text, search):
    """Highlight search terms in text."""
    if not search or not text:
        return text

    text = escape(str(text))
    search = escape(search)
    
    highlighted = text.replace(
        search,
        f'<span class="highlight">{search}</span>',
        flags=re.IGNORECASE
    )
    return mark_safe(highlighted)

@register.filter
def format_address(business):
    """Format a business address."""
    parts = []
    if business.address:
        parts.append(business.address)
    if business.city:
        parts.append(business.city)
    if business.state:
        parts.append(business.state)
    if business.country:
        parts.append(business.country)
    
    return ', '.join(filter(None, parts))

@register.filter
def rating_class(rating):
    """Return Bootstrap class based on rating value."""
    if not rating:
        return 'text-muted'
    
    rating = float(rating)
    if rating >= 4.5:
        return 'text-success'
    elif rating >= 4.0:
        return 'text-primary'
    elif rating >= 3.0:
        return 'text-warning'
    else:
        return 'text-danger'

@register.filter
def truncate_words_with_ellipsis(text, length=50):
    """Truncate text to a certain number of words and add ellipsis."""
    words = str(text).split()
    if len(words) <= length:
        return text
    
    return ' '.join(words[:length]) + '...'

@register.filter
def business_status_badge(business):
    """Return a formatted badge indicating business status."""
    if not business.is_active:
        return mark_safe('<span class="badge bg-danger">Inactive</span>')
    if business.is_verified:
        return mark_safe('<span class="badge bg-success">Verified</span>')
    return mark_safe('<span class="badge bg-warning">Pending Verification</span>')

@register.filter
def amenity_list(business, category=None):
    """Return a formatted list of business amenities."""
    amenities = business.amenities.all()
    if category:
        amenities = amenities.filter(category=category)
    
    if not amenities:
        return ''
    
    result = []
    for amenity in amenities:
        icon = amenity.icon or 'fas fa-check'
        name = escape(amenity.name)
        if amenity.is_highlighted:
            result.append(f'<span class="text-primary"><i class="{icon}"></i> {name}</span>')
        else:
            result.append(f'<i class="{icon}"></i> {name}')
    
    return mark_safe('<br>'.join(result))

@register.filter
def review_count_badge(count):
    """Return a formatted badge for review count."""
    if not count:
        return mark_safe('<span class="badge bg-secondary">No reviews yet</span>')
    
    return mark_safe(f'<span class="badge bg-primary">{count} review{"s" if count != 1 else ""}</span>') 