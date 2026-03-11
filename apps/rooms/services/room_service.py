from django.db.models import Q
from ..models import Room


class RoomService:
    """Service class for room-related operations."""

    @staticmethod
    def get_available_rooms(business_location, check_in_date, check_out_date, guests):
        """
        Get available rooms for the given dates and number of guests.
        """
        return Room.objects.filter(
            business_location=business_location,
            is_available=True,
            maintenance_mode=False,
            max_occupancy__gte=guests
        ).exclude(
            bookings__status__in=['CONFIRMED', 'CHECKED_IN'],
            bookings__check_in_date__lte=check_out_date,
            bookings__check_out_date__gte=check_in_date
        )

    @staticmethod
    def search_rooms(query, location=None):
        """Search rooms by various criteria."""
        queryset = Room.objects.filter(is_available=True)
        
        if location:
            queryset = queryset.filter(business_location=location)
        
        if query:
            queryset = queryset.filter(
                Q(room_type__name__icontains=query) |
                Q(description__icontains=query)
            )
        
        return queryset.select_related('room_type', 'business_location') 