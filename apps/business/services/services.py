from django.db.models import Avg, Count, Q
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.db import transaction

from ..models import (
    Business,
    BusinessLocation,
    BusinessHours,
    BusinessReview,
    BusinessAmenity,
    BusinessAmenityAssignment
)

class BusinessService:
    """Service class for managing businesses."""

    @staticmethod
    def create_business(data, owner):
        """
        Create a new business.
        
        Args:
            data: Dictionary containing business data
            owner: User who owns the business
            
        Returns:
            Business: The created business object
        """
        business = Business.objects.create(
            owner=owner,
            **data
        )
        return business

    @staticmethod
    def update_business(business, data):
        """
        Update an existing business.
        
        Args:
            business: The business to update
            data: Dictionary containing updated business data
            
        Returns:
            Business: The updated business object
        """
        for key, value in data.items():
            setattr(business, key, value)
        business.save()
        return business

class BusinessLocationService:
    """Service class for managing business locations."""

    @staticmethod
    def create_location(data, business):
        """
        Create a new business location.
        
        Args:
            data: Dictionary containing location data
            business: The business this location belongs to
            
        Returns:
            BusinessLocation: The created location object
        """
        location = BusinessLocation.objects.create(
            business=business,
            **data
        )
        return location

    @staticmethod
    def update_location(location, data):
        """
        Update an existing business location.
        
        Args:
            location: The location to update
            data: Dictionary containing updated location data
            
        Returns:
            BusinessLocation: The updated location object
        """
        for key, value in data.items():
            setattr(location, key, value)
        location.save()
        return location

    @staticmethod
    def set_main_location(location):
        """
        Set a location as the main location for its business.
        
        Args:
            location: The location to set as main
            
        Returns:
            BusinessLocation: The updated location object
        """
        with transaction.atomic():
            # Set all other locations of this business as non-main
            BusinessLocation.objects.filter(
                business=location.business
            ).exclude(
                pk=location.pk
            ).update(is_main_location=False)
            
            # Set this location as main
            location.is_main_location = True
            location.save()
        
        return location

class BusinessHoursService:
    """Service class for managing business hours."""

    @staticmethod
    def get_hours_for_location(location):
        """
        Get all business hours for a location.
        
        Args:
            location: The business location
            
        Returns:
            QuerySet: Business hours for the location
        """
        return BusinessHours.objects.filter(
            business_location=location
        ).order_by('day')

    @staticmethod
    def update_hours(location, hours_data):
        """
        Update business hours for a location.
        
        Args:
            location: The business location
            hours_data: Dictionary mapping days to hours data
            
        Returns:
            list: Updated BusinessHours objects
        """
        updated_hours = []
        
        with transaction.atomic():
            for day, data in hours_data.items():
                hours, created = BusinessHours.objects.get_or_create(
                    business_location=location,
                    day=day
                )
                
                for key, value in data.items():
                    setattr(hours, key, value)
                
                hours.full_clean()
                hours.save()
                updated_hours.append(hours)
        
        return updated_hours

class BusinessAmenityService:
    """Service class for managing business amenities."""

    @staticmethod
    def assign_amenities(location, amenities_data):
        """
        Assign amenities to a business location.
        
        Args:
            location: The business location
            amenities_data: List of dictionaries containing amenity data
            
        Returns:
            list: Created BusinessAmenityAssignment objects
        """
        assignments = []
        
        with transaction.atomic():
            # Clear existing assignments
            BusinessAmenityAssignment.objects.filter(
                business_location=location
            ).delete()
            
            # Create new assignments
            for data in amenities_data:
                assignment = BusinessAmenityAssignment.objects.create(
                    business_location=location,
                    **data
                )
                assignments.append(assignment)
        
        return assignments

    @staticmethod
    def get_amenities_for_location(location):
        """
        Get all amenities assigned to a location.
        
        Args:
            location: The business location
            
        Returns:
            QuerySet: Amenity assignments for the location
        """
        return BusinessAmenityAssignment.objects.filter(
            business_location=location,
            is_active=True
        ).select_related('amenity', 'amenity__category')

def get_business_hours(business):
    """
    Get business operating hours grouped by day
    
    Args:
        business (Business): Business instance
    
    Returns:
        dict: Operating hours by day
    """
    hours = BusinessHours.objects.filter(business=business)
    return {hour.get_day_of_week_display(): hour for hour in hours}

def is_business_open(business, time=None):
    """
    Check if a business is currently open
    
    Args:
        business (Business): Business instance
        time (datetime, optional): Time to check. Defaults to current time.
    
    Returns:
        bool: True if business is open, False otherwise
    """
    if time is None:
        time = timezone.localtime()
    
    # Get day of week (0 = Monday, 6 = Sunday)
    day_of_week = time.weekday()
    
    # Check special hours first
    special_hours = business.special_hours.filter(date=time.date()).first()
    if special_hours:
        if special_hours.is_closed:
            return False
        return (special_hours.opening_time <= time.time() < special_hours.closing_time)
    
    # Check regular hours
    regular_hours = business.operating_hours.filter(day_of_week=day_of_week).first()
    if not regular_hours or regular_hours.is_closed:
        return False
        
    return regular_hours.is_open_at(time.time())

def search_businesses(query_params):
    """
    Search businesses based on various criteria
    
    Args:
        query_params (dict): Search parameters
    
    Returns:
        QuerySet: Filtered business queryset
    """
    businesses = Business.objects.filter(is_active=True)
    
    # Apply text search
    if query := query_params.get('query'):
        businesses = businesses.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(city__icontains=query) |
            Q(state__icontains=query)
        )
    
    # Filter by business type
    if business_type := query_params.get('business_type'):
        businesses = businesses.filter(business_type=business_type)
    
    # Filter by city
    if city := query_params.get('city'):
        businesses = businesses.filter(city__iexact=city)
    
    # Filter by minimum rating
    if min_rating := query_params.get('rating'):
        businesses = businesses.annotate(
            avg_rating=Avg('reviews__overall_rating')
        ).filter(avg_rating__gte=float(min_rating))
    
    # Filter verified businesses
    if query_params.get('verified_only'):
        businesses = businesses.filter(is_verified=True)
    
    # Apply sorting
    sort_by = query_params.get('sort_by', 'name')
    if sort_by == 'name':
        businesses = businesses.order_by('name')
    elif sort_by == 'rating':
        businesses = businesses.annotate(
            avg_rating=Avg('reviews__overall_rating')
        ).order_by('-avg_rating', 'name')
    elif sort_by == 'reviews':
        businesses = businesses.annotate(
            review_count=Count('reviews')
        ).order_by('-review_count', 'name')
    
    return businesses.distinct()

def add_business_review(business, user, data):
    """
    Add a review for a business
    
    Args:
        business (Business): Business instance
        user (User): Reviewer
        data (dict): Review data
    
    Returns:
        BusinessReview: Created review instance
    
    Raises:
        ValidationError: If user has already reviewed the business on the given date
    """
    # Check if user has already reviewed this business on the given date
    if BusinessReview.objects.filter(
        business=business,
        user=user,
        visit_date=data['visit_date']
    ).exists():
        raise ValidationError(
            _('You have already reviewed this business for this visit date')
        )
    
    review = BusinessReview.objects.create(
        business=business,
        user=user,
        **data
    )
    return review

def get_business_amenities(business):
    """
    Get all amenities for a business grouped by category
    
    Args:
        business (Business): Business instance
    
    Returns:
        dict: Amenities grouped by category
    """
    assignments = BusinessAmenityAssignment.objects.filter(
        business=business
    ).select_related('amenity', 'amenity__category')
    
    amenities_by_category = {}
    for assignment in assignments:
        category = assignment.amenity.category
        if category not in amenities_by_category:
            amenities_by_category[category] = []
        amenities_by_category[category].append({
            'amenity': assignment.amenity,
            'is_highlighted': assignment.is_highlighted,
            'notes': assignment.notes
        })
    
    return amenities_by_category

def update_business_amenities(business, amenity_data):
    """
    Update amenities for a business
    
    Args:
        business (Business): Business instance
        amenity_data (list): List of dicts containing amenity IDs and optional details
    """
    # Clear existing assignments
    BusinessAmenityAssignment.objects.filter(business=business).delete()
    
    # Create new assignments
    assignments = []
    for item in amenity_data:
        amenity = BusinessAmenity.objects.get(id=item['amenity_id'])
        assignments.append(
            BusinessAmenityAssignment(
                business=business,
                amenity=amenity,
                is_highlighted=item.get('is_highlighted', False),
                notes=item.get('notes', '')
            )
        )
    
    BusinessAmenityAssignment.objects.bulk_create(assignments) 