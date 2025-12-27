from django.db.models import Q
from ..models import RoomType


class RoomTypeService:
    """Service class for room type operations."""

    @staticmethod
    def get_active_room_types():
        """Get all active room types."""
        return RoomType.objects.filter(is_active=True).order_by('name')

    @staticmethod
    def search_room_types(query):
        """Search room types by name or code."""
        return RoomType.objects.filter(
            is_active=True
        ).filter(
            Q(name__icontains=query) |
            Q(code__icontains=query)
        ).order_by('name')

    @staticmethod
    def get_room_type_by_code(code):
        """Get room type by its code."""
        try:
            return RoomType.objects.get(code=code, is_active=True)
        except RoomType.DoesNotExist:
            return None

    @staticmethod
    def get_room_types_with_availability(business_location, check_in_date, check_out_date):
        """Get room types with availability information for given dates."""
        from ..models import Room
        
        room_types = RoomType.objects.filter(
            is_active=True,
            rooms__business_location=business_location,
            rooms__is_available=True,
            rooms__maintenance_mode=False
        ).distinct()

        # Add availability count for each room type
        for room_type in room_types:
            available_rooms = Room.objects.filter(
                room_type=room_type,
                business_location=business_location,
                is_available=True,
                maintenance_mode=False
            ).exclude(
                bookings__status__in=['CONFIRMED', 'CHECKED_IN'],
                bookings__check_in_date__lte=check_out_date,
                bookings__check_out_date__gte=check_in_date
            )
            room_type.available_count = available_rooms.count()

        return room_types 